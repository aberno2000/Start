#include <nlohmann/json.hpp>
using json = nlohmann::json;

#include "../include/DataHandling/HDF5Handler.hpp"
#include "../include/ParticleTracker.hpp"

void ParticleTracker::checkMeshfilename() const
{
    if (m_config.getMeshFilename() == "")
    {
        ERRMSG("Can't open mesh file: Name of the file is empty");
        throw std::runtime_error("");
    }

    if (!util::exists(m_config.getMeshFilename()))
    {
        ERRMSG(util::stringify("Can't open mesh file: There is no such file with name: ", m_config.getMeshFilename()));
        throw std::runtime_error("");
    }

    if (!m_config.getMeshFilename().ends_with(".msh"))
    {
        ERRMSG(util::stringify("Can't open mesh file: Format of the file must be .msh. Current filename: ", m_config.getMeshFilename()));
        throw std::runtime_error("");
    }
}

void ParticleTracker::initializeSurfaceMesh() { _triangleMesh = Mesh::getMeshParams(m_config.getMeshFilename()); }

void ParticleTracker::initializeSurfaceMeshAABB()
{
    if (_triangleMesh.empty())
    {
        ERRMSG("Can't construct AABB for triangle mesh - surface mesh is empty");
        throw std::runtime_error("");
    }

    for (auto const &meshParam : _triangleMesh)
    {
        auto const &triangle{std::get<1>(meshParam)};
        if (!triangle.is_degenerate())
            _triangles.emplace_back(triangle);
    }

    if (_triangles.empty())
    {
        ERRMSG("Can't create AABB for triangle mesh - triangles from the mesh are invalid. Possible reason: all the triangles are degenerate")
        throw std::runtime_error("");
    }

    _surfaceMeshAABBtree = AABB_Tree_Triangle(std::cbegin(_triangles), std::cend(_triangles));
}

void ParticleTracker::initializeParticles()
{
    m_particles = createParticlesWithEnergy(m_config.getParticlesCount(),
                                            m_config.getProjective(),
                                            m_config.getEnergy(),
                                            util::getParticleSourceCoordsAndDirection());
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

void ParticleTracker::startSimulation()
{
    /* Beginning of the FEM initialization. */
    // Assemblying global stiffness matrix from the mesh file.
    GSMatrixAssemblier assemblier(m_config.getMeshFilename(), m_config.getDesiredCalculationAccuracy(), m_config.getNullBoundaryNodes());

    // PIC: Creating cubic grid for the tetrahedron mesh.
    Grid3D cubicGrid(assemblier.getMeshComponents(), m_config.getEdgeSize());

    // Setting boundary conditions.
    std::map<GlobalOrdinal, double> boundaryConditions;
    for (auto const &[nodeIds, value] : m_config.getBoundaryConditions())
        for (GlobalOrdinal nodeId : nodeIds)
            boundaryConditions[nodeId] = value;
    assemblier.setBoundaryConditions(boundaryConditions);
    // assemblier.print();

    SolutionVector solutionVector(assemblier.rows(), kdefault_polynomOrder);
    solutionVector.clear();
    /* Ending of the FEM initialization. */

    // Tracking particles inside the tetrahedrons.
    for (double t{}; t <= m_config.getSimulationTime(); t += m_config.getTimeStep())
    {
        /* (Tetrahedron ID | Particles inside) */
        std::map<size_t, ParticleVector> PICtracker; // Map to managing in which tetrahedron how many and which particles are in the time moment `t`.

        /* (Tetrahedron ID | Charge density in coulumbs) */
        std::map<size_t, double> tetrahedronChargeDensityMap;

        /* (Node ID | Charge in coulumbs) */
        std::map<GlobalOrdinal, double> nodeChargeDensityMap;

        for (Particle const &particle : m_particles)
        {
            // Determine which tetrahedrons the particle may intersect based on its grid index.
            auto meshParams{cubicGrid.getTetrahedronsByGridIndex(cubicGrid.getGridIndexByPosition(particle.getCentre()))};
            for (auto const &meshParam : meshParams)
                if (isPointInsideTetrahedron(particle.getCentre(), meshParam.tetrahedron))
                    PICtracker[meshParam.globalTetraId].emplace_back(particle);
        }

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
                nodeChargeDensityMap[nodeId] = totalCharge / totalVolume;
        }

        std::cout << "Charge density in nodes:\n";
        for (auto const &[nodeId, chargeDensity] : nodeChargeDensityMap)
            std::cout << std::format("Node[{}] : {} C/m³\n", nodeId, chargeDensity);

        /* Remains FEM. */
        // Creating solution vector, filling it with the random values, and applying boundary conditions.
        auto nonChangebleNodes{m_config.getNonChangeableNodes()};
        for (auto const &[nodeId, nodeChargeDensity] : nodeChargeDensityMap)
            if (std::ranges::find(nonChangebleNodes, nodeId) == nonChangebleNodes.cend())
                boundaryConditions[nodeId] = nodeChargeDensity;
        solutionVector.setBoundaryConditions(boundaryConditions);
        // solutionVector.print();

        // Solve the equation Ax=b.
        MatrixEquationSolver solver(assemblier, solutionVector);
        auto solverParams{solver.createSolverParams(m_config.getSolverName(), m_config.getMaxIterations(), m_config.getConvergenceTolerance(),
                                                    m_config.getVerbosity(), m_config.getOutputFrequency(), m_config.getNumBlocks(), m_config.getBlockSize(),
                                                    m_config.getMaxRestarts(), m_config.getFlexibleGMRES(), m_config.getOrthogonalization(),
                                                    m_config.getAdaptiveBlockSize(), m_config.getConvergenceTestFrequency())};
        solver.solve(m_config.getSolverName(), solverParams);
        solver.calculateElectricField(); // Getting electric field for the each cell.

        // Writing to electric and potential fields to files just ones.
        if (t == 0.0)
        {
            // Gathering results from the solution of the equation Ax=b to the GMSH .pos file.
            solver.writeElectricPotentialsToPosFile();

            // Making vectors of electrical field for all the tetrahedra in GMSH .pos file.
            solver.writeElectricFieldVectorsToPosFile();
        }

        // EM-pushgin particle with Boris Integrator.
        MathVector magneticInduction{}; // For brevity assuming that induction vector B is 0.
        for (Particle &particle : m_particles)
        {
            // If set contains specified particle ID - skip checking this particle.
            if (_settledParticlesIds.find(particle.getId()) != _settledParticlesIds.cend())
                continue;

            // Finding tetrahedron that containing this particle.
            size_t containingTetrahedron{};
            for (auto const &[tetraId, particlesInside] : PICtracker)
            {
                if (std::ranges::find_if(particlesInside, [&particle](Particle const &storedParticle)
                                         { return particle.getId() == storedParticle.getId(); }) != particlesInside.cend())
                {
                    containingTetrahedron = tetraId;
                    break; // If particle was found inside certain tetrahedron - breaking down the loop.
                }
            }

            // Updating velocity according to the EM-field.
            if (auto tetrahedron{assemblier.getMeshComponents().getMeshDataByTetrahedronId(containingTetrahedron)})
                if (tetrahedron->electricField.has_value())
                    particle.electroMagneticPush(magneticInduction,
                                                 MathVector(tetrahedron->electricField->x(), tetrahedron->electricField->y(), tetrahedron->electricField->z()),
                                                 m_config.getTimeStep());

            // Updating positions for all the particles.
            m_particlesMovement[particle.getId()].emplace_back(particle.getCentre());
            Point prev(particle.getCentre()); // Saving previous particle position before updating the position.
            particle.updatePosition(m_config.getTimeStep());
            Ray ray(prev, particle.getCentre());

            // Check ray on degeneracy.
            if (ray.is_degenerate())
                continue;

            /* Gas collision part. */
            particle.colide(m_config.getGas(), _gasConcentration, m_config.getScatteringModel(), m_config.getTimeStep()); // Updating velocity according to gas collision.

            // Check intersection of ray with mesh.
            auto intersection{_surfaceMeshAABBtree.any_intersection(ray)};
            if (!intersection)
                continue;

            // Getting triangle object.
            auto triangle{boost::get<Triangle>(*intersection->second)};

            // Check if some of sides of angles in the triangle <= 0 (check on degeneracy).
            if (triangle.is_degenerate())
                continue;

            // Finding matching triangle in the mesh.
            auto matchedIt{std::ranges::find_if(_triangleMesh, [triangle](auto const &el)
                                                { return triangle == std::get<1>(el); })};
            if (matchedIt != _triangleMesh.cend())
            {
                size_t id{isRayIntersectTriangle(ray, *matchedIt)};
                if (id != -1ul)
                {
                    ++_settledParticlesCounterMap[id];             // Filling map to detect how much particles settled on certain triangle.
                    _settledParticlesIds.insert(particle.getId()); // Remembering settled particle ID.
                }
            }
        }
    }

    updateSurfaceMesh();
}
