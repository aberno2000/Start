#include <algorithm>
#include <atomic>
#include <execution>
#include <future>
#include <nlohmann/json.hpp>
using json = nlohmann::json;

#include "../include/DataHandling/HDF5Handler.hpp"
#include "../include/ParticleTracker.hpp"

std::mutex ParticleTracker::m_PICTracker_mutex;
std::mutex ParticleTracker::m_nodeChargeDensityMap_mutex;
std::mutex ParticleTracker::m_particlesMovement_mutex;
std::mutex ParticleTracker::m_settledParticles_mutex;
std::atomic_flag ParticleTracker::m_stop_processing = ATOMIC_FLAG_INIT;

void ParticleTracker::checkMeshfilename() const
{
    if (m_config.getMeshFilename() == "")
        throw std::runtime_error("Can't open mesh file: Name of the file is empty");

    if (!util::exists(m_config.getMeshFilename()))
        throw std::runtime_error(util::stringify("Can't open mesh file: There is no such file with name: ", m_config.getMeshFilename()));

    if (!m_config.getMeshFilename().ends_with(".msh"))
        throw std::runtime_error(util::stringify("Can't open mesh file: Format of the file must be .msh. Current filename: ", m_config.getMeshFilename()));
}

void ParticleTracker::initializeSurfaceMesh() { _triangleMesh = Mesh::getMeshParams(m_config.getMeshFilename()); }

void ParticleTracker::initializeSurfaceMeshAABB()
{
    if (_triangleMesh.empty())
        throw std::runtime_error("Can't construct AABB for triangle mesh - surface mesh is empty");

    for (auto const &meshParam : _triangleMesh)
    {
        auto const &triangle{std::get<1>(meshParam)};
        if (!triangle.is_degenerate())
            _triangles.emplace_back(triangle);
    }

    if (_triangles.empty())
        throw std::runtime_error("Can't create AABB for triangle mesh - triangles from the mesh are invalid. Possible reason: all the triangles are degenerate");

    _surfaceMeshAABBtree = AABB_Tree_Triangle(std::cbegin(_triangles), std::cend(_triangles));
}

void ParticleTracker::initializeParticles()
{
    if (m_config.isParticleSourcePoint())
    {
        auto tmp{createParticlesFromPointSource(m_config.getParticleSourcePoints())};
        if (!tmp.empty())
            m_particles.insert(m_particles.end(), std::ranges::begin(tmp), std::ranges::end(tmp));
    }
    if (m_config.isParticleSourceSurface())
    {
        auto tmp{createParticlesFromSurfaceSource(m_config.getParticleSourceSurfaces())};
        if (!tmp.empty())
            m_particles.insert(m_particles.end(), std::ranges::begin(tmp), std::ranges::end(tmp));
    }

    if (m_particles.empty())
        throw std::runtime_error("Particles are uninitialized, check your configuration file");
}

void ParticleTracker::initialize()
{
    initializeSurfaceMesh();
    initializeSurfaceMeshAABB();
}

bool ParticleTracker::isPointInsideTetrahedron(Point const &point, Tetrahedron const &tetrahedron)
{
    CGAL::Oriented_side oriented_side{tetrahedron.oriented_side(point)};
    if (oriented_side == CGAL::ON_POSITIVE_SIDE)
        return true;
    else if (oriented_side == CGAL::ON_NEGATIVE_SIDE)
        return false;
    else
        // TODO: Correctly handle case when particle is on boundary of tetrahedron.
        return true;
}

size_t ParticleTracker::isRayIntersectTriangle(Ray const &ray, MeshTriangleParam const &triangle)
{
    // Returning invalid index if ray or triangle is degenerate
    if (std::get<1>(triangle).is_degenerate() || ray.is_degenerate())
        return -1ul;

    return (RayTriangleIntersection::isIntersectTriangle(ray, std::get<1>(triangle)))
               ? std::get<0>(triangle)
               : -1ul;
}

void ParticleTracker::saveParticleMovements() const
{
    try
    {
        if (m_particlesMovement.empty())
        {
            std::cerr << "Warning: Particle movements map is empty, no data to save." << std::endl;
            return;
        }

        json j;
        for (const auto &[id, movements] : m_particlesMovement)
        {
            json positions;
            for (auto const &point : movements)
                positions.push_back({{"x", point.x()}, {"y", point.y()}, {"z", point.z()}});
            j[std::to_string(id)] = positions;
        }

        std::ofstream file("particles_movements.json");
        if (file.is_open())
        {
            file << j.dump(4); // 4 spaces indentation for pretty printing
            file.close();
        }
        else
            throw std::ios_base::failure("Failed to open file for writing");
    }
    catch (std::ios_base::failure const &e)
    {
        std::cerr << "I/O error occurred: " << e.what() << std::endl;
    }
    catch (json::exception const &e)
    {
        std::cerr << "JSON error occurred: " << e.what();
    }
}

void ParticleTracker::updateSurfaceMesh()
{
    // Updating hdf5file to know how many particles settled on certain triangle from the surface mesh.
    auto mapEnd{_settledParticlesCounterMap.cend()};
    for (auto &meshParam : _triangleMesh)
        if (auto it{_settledParticlesCounterMap.find(std::get<0>(meshParam))}; it != mapEnd)
            std::get<3>(meshParam) = it->second;

    std::string hdf5filename(std::string(m_config.getMeshFilename().substr(0ul, m_config.getMeshFilename().find("."))));
    hdf5filename += ".hdf5";
    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(_triangleMesh);
}

ParticleTracker::ParticleTracker(std::string_view config_filename) : m_config(config_filename)
{
    // Checking mesh filename on validity and assign it to the class member.
    checkMeshfilename();

    // Calculating and checking gas concentration.
    _gasConcentration = util::calculateConcentration(config_filename);
    if (_gasConcentration < constants::gasConcentrationMinimalValue)
        WARNINGMSG(util::stringify("Something wrong with the concentration of the gas. Its value is ", _gasConcentration, ". Simulation might considerably slows down"));

    // Initializing all the objects from the mesh.
    initialize();

    // Spawning particles.
    initializeParticles();
}

void ParticleTracker::processPIC(size_t start_index, size_t end_index,
                                 Grid3D const &cubicGrid, GSMatrixAssemblier &assemblier,
                                 std::map<size_t, ParticleVector> &globalPICtracker,
                                 std::map<GlobalOrdinal, double> &nodeChargeDensityMap)
{
    std::map<size_t, ParticleVector> PICtracker;
    std::map<size_t, double> tetrahedronChargeDensityMap;

    std::for_each(m_particles.begin() + start_index, m_particles.begin() + end_index, [this, cubicGrid, &PICtracker](auto &particle)
                  {
        if (_settledParticlesIds.find(particle.getId()) != _settledParticlesIds.cend())
            return;

        auto meshParams{cubicGrid.getTetrahedronsByGridIndex(cubicGrid.getGridIndexByPosition(particle.getCentre()))};
        for (auto const &meshParam : meshParams)
            if (isPointInsideTetrahedron(particle.getCentre(), meshParam.tetrahedron))
                PICtracker[meshParam.globalTetraId].emplace_back(particle); });

    // Calculating charge density in each of the tetrahedron using `PICtracker`.
    for (auto const &[tetrId, particlesInside] : PICtracker)
        tetrahedronChargeDensityMap.insert({tetrId,
                                            (std::accumulate(particlesInside.cbegin(), particlesInside.cend(), 0.0, [](double sum, Particle const &particle)
                                                             { return sum + particle.getCharge(); })) /
                                                assemblier.getMeshComponents().getMeshDataByTetrahedronId(tetrId).value().tetrahedron.volume()});

    // Go around each node and aggregate data from adjacent tetrahedra.
    for (auto const &[nodeId, adjecentTetrahedrons] : assemblier.getMeshComponents().getNodeTetrahedronsMap())
    {
        double totalCharge{}, totalVolume{};

        // Sum up the charge and volume for all tetrahedra of a given node.
        for (auto const &tetrId : adjecentTetrahedrons)
        {
            if (tetrahedronChargeDensityMap.find(tetrId) != tetrahedronChargeDensityMap.end())
            {
                double tetrahedronChargeDensity{tetrahedronChargeDensityMap.at(tetrId)},
                    tetrahedronVolume{assemblier.getMeshComponents().getMeshDataByTetrahedronId(tetrId)->tetrahedron.volume()};

                totalCharge += tetrahedronChargeDensity * tetrahedronVolume;
                totalVolume += tetrahedronVolume;
            }
        }

        // Calculate and store the charge density for the node.
        if (totalVolume > 0)
        {
            std::lock_guard<std::mutex> lock(m_nodeChargeDensityMap_mutex);
            nodeChargeDensityMap[nodeId] = totalCharge / totalVolume;
        }
    }

    // Adding all the elements from this thread from this local PICTracker to the global PIC tracker.
    std::lock_guard<std::mutex> lock_PIC(m_PICTracker_mutex);
    for (auto const &[tetraId, particlesInside] : PICtracker)
    {
        auto &globalParticles{globalPICtracker[tetraId]};
        globalParticles.insert(globalParticles.begin(), particlesInside.begin(), particlesInside.end());
    }
}

void ParticleTracker::solveEquation(std::map<GlobalOrdinal, double> &nodeChargeDensityMap,
                                    GSMatrixAssemblier &assemblier, SolutionVector &solutionVector,
                                    std::map<GlobalOrdinal, double> &boundaryConditions, double time)
{
    auto nonChangebleNodes{m_config.getNonChangeableNodes()};
    for (auto const &[nodeId, nodeChargeDensity] : nodeChargeDensityMap)
        if (std::ranges::find(nonChangebleNodes, nodeId) == nonChangebleNodes.cend())
            boundaryConditions[nodeId] = nodeChargeDensity;
    solutionVector.setBoundaryConditions(boundaryConditions);

    std::unique_ptr<MatrixEquationSolver> solver;
    {
        solver = std::make_unique<MatrixEquationSolver>(assemblier, solutionVector);

        auto solverParams{solver->createSolverParams(m_config.getSolverName(), m_config.getMaxIterations(), m_config.getConvergenceTolerance(),
                                                     m_config.getVerbosity(), m_config.getOutputFrequency(), m_config.getNumBlocks(), m_config.getBlockSize(),
                                                     m_config.getMaxRestarts(), m_config.getFlexibleGMRES(), m_config.getOrthogonalization(),
                                                     m_config.getAdaptiveBlockSize(), m_config.getConvergenceTestFrequency())};
        solver->solve(m_config.getSolverName(), solverParams);
        solver->calculateElectricField(); // Getting electric field for the each cell.

        solver->writeElectricPotentialsToPosFile(time);
        solver->writeElectricFieldVectorsToPosFile(time);
    }
}

void ParticleTracker::processSurfaceCollisionTracker(size_t start_index, size_t end_index,
                                                     Grid3D const &cubicGrid, GSMatrixAssemblier const &assemblier,
                                                     std::map<size_t, ParticleVector> const &PICtracker, double t)
{
    MathVector magneticInduction{}; // For brevity assuming that induction vector B is 0.
    std::for_each(m_particles.begin() + start_index, m_particles.begin() + end_index,
                  [this, cubicGrid, PICtracker, assemblier, magneticInduction, t](auto &particle)
                  {
                      {
                          std::lock_guard<std::mutex> lock(m_settledParticles_mutex);
                          if (_settledParticlesIds.find(particle.getId()) != _settledParticlesIds.cend())
                              return;
                      }

                      size_t containingTetrahedron{};
                      for (auto const &[tetraId, particlesInside] : PICtracker)
                      {
                          if (std::ranges::find_if(particlesInside, [particle](Particle const &storedParticle)
                                                   { return particle.getId() == storedParticle.getId(); }) != particlesInside.cend())
                          {
                              containingTetrahedron = tetraId;
                              break;
                          }
                      }

                      if (auto tetrahedron{assemblier.getMeshComponents().getMeshDataByTetrahedronId(containingTetrahedron)})
                          if (tetrahedron->electricField.has_value())
                              particle.electroMagneticPush(magneticInduction,
                                                           MathVector(tetrahedron->electricField->x(), tetrahedron->electricField->y(), tetrahedron->electricField->z()),
                                                           m_config.getTimeStep());

                      Point prev(particle.getCentre());
                      particle.updatePosition(m_config.getTimeStep());
                      Ray ray(prev, particle.getCentre());

                      if (ray.is_degenerate())
                          return;

                      particle.colide(m_config.getGas(), _gasConcentration, m_config.getScatteringModel(), m_config.getTimeStep());

                      // There is no need to check particle collision with surface mesh in initial time moment of the simulation (when t = 0).
                      if (t == 0.0)
                          return;

                      auto intersection{_surfaceMeshAABBtree.any_intersection(ray)};
                      if (!intersection)
                          return;

                      auto triangle{boost::get<Triangle>(*intersection->second)};
                      if (triangle.is_degenerate())
                          return;

                      auto matchedIt{std::ranges::find_if(_triangleMesh, [triangle](auto const &el)
                                                          { return triangle == std::get<1>(el); })};
                      if (matchedIt != _triangleMesh.cend())
                      {
                          size_t id{isRayIntersectTriangle(ray, *matchedIt)};
                          if (id != -1ul)
                          {
                              std::lock_guard<std::mutex> lock(m_settledParticles_mutex);
                              ++_settledParticlesCounterMap[id];
                              _settledParticlesIds.insert(particle.getId());

                              if (_settledParticlesIds.size() >= m_particles.size())
                              {
                                  m_stop_processing.test_and_set();
                                  return;
                              }
                          }
                      }

                      {
                          std::lock_guard<std::mutex> lock(m_particlesMovement_mutex);
                          if (_settledParticlesIds.find(particle.getId()) == _settledParticlesIds.cend())
                              m_particlesMovement[particle.getId()].emplace_back(particle.getCentre());
                      }
                  });
}

void ParticleTracker::processSegment(size_t start_index, size_t end_index,
                                     Grid3D const &cubicGrid, GSMatrixAssemblier &assemblier, SolutionVector &solutionVector,
                                     std::map<GlobalOrdinal, double> &boundaryConditions, std::map<GlobalOrdinal, double> &nodeChargeDensityMap,
                                     std::barrier<> &barrier)
{
    for (double t{};
         t <= m_config.getSimulationTime() && !m_stop_processing.test();
         t += m_config.getTimeStep())
    {
        std::map<size_t, ParticleVector> globalPICtracker; /* (Tetrahedron ID | Particles inside) */

        // 1. Obtain charge densities in all the nodes.
        processPIC(start_index, end_index, cubicGrid, assemblier, globalPICtracker, nodeChargeDensityMap);

        barrier.arrive_and_wait(); // Wait for all threads to complete PIC.

        // 2. Solving equation Ax=b.
        std::call_once(m_solve_once_flag, &ParticleTracker::solveEquation, this,
                       std::ref(nodeChargeDensityMap), std::ref(assemblier), std::ref(solutionVector), std::ref(boundaryConditions), t);

        barrier.arrive_and_wait(); // Wait for the equation to be solved.

        // 3. Receiving particles those are colided with surface.
        processSurfaceCollisionTracker(start_index, end_index, cubicGrid, assemblier, globalPICtracker, t);
    }
}

void ParticleTracker::startSimulation()
{
    /* Beginning of the FEM initialization. */
    // Assemblying global stiffness matrix from the mesh file.
    GSMatrixAssemblier assemblier(m_config.getMeshFilename(), m_config.getDesiredCalculationAccuracy());

    // PIC: Creating cubic grid for the tetrahedron mesh.
    Grid3D cubicGrid(assemblier.getMeshComponents(), m_config.getEdgeSize());

    // Setting boundary conditions.
    std::map<GlobalOrdinal, double> boundaryConditions;
    for (auto const &[nodeIds, value] : m_config.getBoundaryConditions())
        for (GlobalOrdinal nodeId : nodeIds)
            boundaryConditions[nodeId] = value;
    assemblier.setBoundaryConditions(boundaryConditions);

    SolutionVector solutionVector(assemblier.rows(), kdefault_polynomOrder);
    solutionVector.clear();
    /* Ending of the FEM initialization. */

    if (auto curThreads{m_config.getNumThreads()}; curThreads < 1 || curThreads > std::thread::hardware_concurrency())
        throw std::runtime_error("The number of threads requested (1) exceeds the number of hardware threads supported by the system (" +
                                 std::to_string(curThreads) +
                                 "). Please run on a system with more resources.");

    unsigned int num_threads{m_config.getNumThreads()},
        hardware_threads{std::thread::hardware_concurrency()},
        threshold{static_cast<unsigned int>(hardware_threads * 0.8)};
    if (num_threads > threshold)
        WARNINGMSG(util::stringify("Warning: The number of threads requested (", num_threads,
                                   ") is close to or exceeds 80% of the available hardware threads (", hardware_threads, ").",
                                   " This might cause the system to slow down or become unresponsive because the system also needs resources for its own tasks."));

    // Number of concurrent threads supported by the implementation.
    std::vector<std::future<void>> futures;
    std::map<GlobalOrdinal, double> nodeChargeDensityMap;

    std::barrier barrier(num_threads);

    // Separate on segments.
    size_t particles_per_thread{m_particles.size() / num_threads},
        start_index{};
    size_t managed_particles{particles_per_thread * num_threads}; // Count of the managed particles.

    // Create threads and assign each a segment of particles to process.
    for (size_t i{}; i < num_threads; ++i)
    {
        size_t end_index{(i == num_threads - 1) ? m_particles.size() : start_index + particles_per_thread};

        // If for example simulation started with 1'000 particles and 18 threads - we lost 10 particles: 1000/18=55 => 55*18=990.
        // In this case we assign all remain particles to the last thread to manage them.
        if (i == num_threads - 1 && managed_particles < m_particles.size())
            end_index = m_particles.size();

        futures.emplace_back(std::async(std::launch::async, [this, start_index, end_index,
                                                             cubicGrid, &assemblier, &solutionVector, &boundaryConditions,
                                                             &nodeChargeDensityMap, &barrier]()
                                        { this->processSegment(start_index, end_index,
                                                               cubicGrid, assemblier, solutionVector, boundaryConditions,
                                                               nodeChargeDensityMap, barrier); }));
        start_index = end_index;
    }

    // Wait for all threads to complete their work.
    for (auto &f : futures)
        f.get();

    updateSurfaceMesh();
}
