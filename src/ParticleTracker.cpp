#include "../include/ParticleTracker.hpp"

static constexpr ParticleType k_gas{particle_types::Ar};
static constexpr double k_gas_concentration{10e26};
static constexpr std::string_view k_scattering_model{"HS"};

void ParticleTracker::checkMeshfilename(std::string_view mesh_filename) const
{
    if (mesh_filename == "")
    {
        ERRMSG("Can't open mesh file: Name of the file is empty");
        throw std::runtime_error("");
    }

    if (!util::exists(mesh_filename))
    {
        ERRMSG(util::stringify("Can't open mesh file: There is no such file with name: ", mesh_filename));
        throw std::runtime_error("");
    }

    if (!mesh_filename.ends_with(".msh"))
    {
        ERRMSG(util::stringify("Can't open mesh file: Format of the file must be .msh. Current filename: ", mesh_filename));
        throw std::runtime_error("");
    }
}

void ParticleTracker::initializeSurfaceMesh() { _triangleMesh = Mesh::getMeshParams(m_mesh_filename); }

void ParticleTracker::initializeSurfaceMeshAABB()
{
    if (_triangleMesh.empty())
    {
        ERRMSG("Can't construct AABB for triangle mesh - surface mesh is empty");
        throw std::runtime_error("");
    }

    TriangleVector triangles;
    for (auto const &meshParam : _triangleMesh)
    {
        auto const &triangle{std::get<1>(meshParam)};
        if (!triangle.is_degenerate())
            triangles.emplace_back(triangle);
    }

    if (triangles.empty())
    {
        ERRMSG("Can't create AABB for triangle mesh - triangles from the mesh are invalid. Possible reason: all the triangles are degenerate")
        throw std::runtime_error("");
    }

    _surfaceMeshAABBtree = AABB_Tree_Triangle(std::cbegin(triangles), std::cend(triangles));
}

void ParticleTracker::initializeVolumeMesh() { _tetrahedronMesh = Mesh::getTetrahedronMeshParams(m_mesh_filename); }

void ParticleTracker::initializeNodeTetrahedronMap() { _nodeTetraMap = Mesh::getNodeTetrahedronsMap(m_mesh_filename); }

void ParticleTracker::initializeBoundaryNodes() { _boundaryNodes = Mesh::getTetrahedronMeshBoundaryNodes(m_mesh_filename); }

void ParticleTracker::initializeParticles(ParticleType const &particleType, size_t count)
{
    m_particles = createParticlesWithVelocities(count, particleType,
                                                100, 100, 100,
                                                200, 200, 200,
                                                -100, -100, -100,
                                                100, 100, 100);
}

void ParticleTracker::initialize()
{
    initializeSurfaceMesh();
    initializeSurfaceMeshAABB();
    initializeVolumeMesh();
    initializeNodeTetrahedronMap();
    initializeBoundaryNodes();
}

bool ParticleTracker::isPointInsideTetrahedron(Point const &point, MeshTetrahedronParam const &meshParam)
{
    CGAL::Oriented_side oriented_side{std::get<1>(meshParam).oriented_side(point)};
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
    return (RayTriangleIntersection::isIntersectTriangle(ray, std::get<1>(triangle)))
               ? std::get<0>(triangle)
               : -1ul;
}

ParticleTracker::ParticleTracker(std::string_view mesh_filename)
{
    // Checking mesh filename on validity and assign it to the class member.
    checkMeshfilename(mesh_filename);
    m_mesh_filename = mesh_filename;

    // Initializing all the objects from the mesh.
    initialize();
}

void ParticleTracker::startSimulation(ParticleType const &particleType, size_t particleCount,
                                      double edgeSize, short desiredAccuracy,
                                      double time_step, double simulation_time)
{
    if (desiredAccuracy <= 0)
        throw std::runtime_error("Calculation accuracy can't be <= 0. Specified value is: " + std::to_string(desiredAccuracy));

    _desiredAccuracy = desiredAccuracy;
    initializeParticles(particleType, particleCount);

    // Creating cubic grid for the tetrahedron mesh.
    Grid3D cubicGrid(_tetrahedronMesh, edgeSize);

    /* Beginning of the FEM initialization. */
    // Assemblying global stiffness matrix from the mesh file.
    GSMatrixAssemblier assemblier(m_mesh_filename, kdefault_polynomOrder, _desiredAccuracy);

    // Setting boundary conditions.
    // *Boundary conditions for box: 300x300x700, mesh size: 1.
    std::map<GlobalOrdinal, double> boundaryConditions;
    for (size_t nodeId : /* _boundaryNodes */
         {2, 4, 6, 8, 28, 29, 30, 59, 60, 61, 50, 51, 52, 53, 54, 55,
          215, 201, 206, 211, 203, 205, 207, 209, 204, 210, 214, 202, 208, 213, 212})
        boundaryConditions[nodeId] = 0.0;
    for (GlobalOrdinal nodeId : {1, 3, 5, 7, 17, 18, 19, 39, 40, 41, 56, 57, 58, 62, 63, 64, 230,
                                 216, 221, 226, 224, 218, 220, 222, 225, 229, 217, 228, 223, 219, 227})
        boundaryConditions[nodeId] = 1.0;

    assemblier.setBoundaryConditions(boundaryConditions);
    assemblier.print(); // 3_opt. Printing the matrix.

    SolutionVector solutionVector(assemblier.rows(), kdefault_polynomOrder);
    solutionVector.clear();
    /* Ending of the FEM initialization. */

    // Tracking particles inside the tetrahedrons.
    for (double t{}; t <= simulation_time; t += time_step)
    {
        std::cout << std::format("\033[1;34mTime {} s\n\033[0m", t);

        /* (Tetrahedron ID | Particles inside) */
        std::map<size_t, ParticleVector> PICtracker; // Map to managing in which tetrahedron how many and which particles are in the time moment `t`.

        /* (Tetrahedron ID | Charge density in coulumbs) */
        std::map<size_t, double> tetrahedronChargeDensityMap;

        /* (Node ID | Charge in coulumbs) */
        std::map<GlobalOrdinal, double> nodeChargeDensityMap;

        /* (Triangle ID | Counter of settled particle in this triangle) */
        std::map<size_t, int> settledParticlesCounterMap;

        // For each time step managing movement of each particle.
        for (Particle const &particle : m_particles)
        {
            // Determine which tetrahedrons the particle may intersect based on its grid index.
            auto meshParams{cubicGrid.getTetrahedronsByGridIndex(cubicGrid.getGridIndexByPosition(particle.getCentre()))};
            for (auto const &meshParam : meshParams)
                if (isPointInsideTetrahedron(particle.getCentre(), meshParam))
                    PICtracker[std::get<0>(meshParam)].emplace_back(particle);
        }

        // Calculating charge density in each of the tetrahedron using `PICtracker`.
        for (auto const &[tetrId, particlesInside] : PICtracker)
            tetrahedronChargeDensityMap.insert({tetrId,
                                                (std::accumulate(particlesInside.cbegin(), particlesInside.cend(), 0.0, [](double sum, Particle const &particle)
                                                                 { return sum + particle.getCharge(); })) /
                                                    (std::get<2>(cubicGrid.getTetrahedronMeshParamById(tetrId)) * 1e-9)}); // mm³ to m³.

        std::cout << "Charge density in tetrahedrons:\n";
        for (auto const &[tetrId, tetrDensity] : tetrahedronChargeDensityMap)
            std::cout << std::format("Tetrahedron[{}]: {} C/m³\n", tetrId, tetrDensity);

        // Go around each node and aggregate data from adjacent tetrahedra.
        for (auto const &[nodeId, adjecentTetrahedrons] : _nodeTetraMap)
        {
            double totalCharge{}, totalVolume{};

            // Sum up the charge and volume for all tetrahedra of a given node.
            for (auto const &tetrId : adjecentTetrahedrons)
            {
                if (tetrahedronChargeDensityMap.find(tetrId) != tetrahedronChargeDensityMap.end())
                {
                    double tetrahedronChargeDensity{tetrahedronChargeDensityMap.at(tetrId)},
                        tetrahedronVolume{std::get<2>(cubicGrid.getTetrahedronMeshParamById(tetrId)) * 1e-9}; // mm³ в m³.

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
        for (auto const &[nodeId, nodeChargeDensity] : nodeChargeDensityMap)
            boundaryConditions[nodeId] = nodeChargeDensity;
        solutionVector.setBoundaryConditions(boundaryConditions);
        solutionVector.print(); // 4_opt. Printing the solution vector.

        // Solve the equation Ax=b.
        MatrixEquationSolver solver(assemblier, solutionVector);
        solver.solveAndPrint();
        solver.printLHS();

        // Writing to electric and potential fields to files just ones.
        if (t == 0.0)
        {
            // Gathering results from the solution of the equation Ax=b to the GMSH .pos file.
            solver.writeElectricPotentialsToPosFile();

            // Making vectors of electrical field for all the tetrahedra in GMSH .pos file.
            solver.writeElectricFieldVectorsToPosFile();
        }

        // EM-pushgin particle with Boris Integrator.
        MathVector magneticInduction{};                      // For brevity assuming that induction vector B is 0.
        auto electricFieldMap{solver.getElectricFieldMap()}; // Getting electric field for the each cell.
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
            if (electricFieldMap.find(containingTetrahedron) != electricFieldMap.cend())
                particle.electroMagneticPush(magneticInduction, electricFieldMap.at(containingTetrahedron), time_step);

            // Updating positions for all the particles.
            Point prev(particle.getCentre()); // Saving previous particle position before updating the position.
            particle.updatePosition(time_step);

            /* Gas collision part. */
            particle.colide(k_gas, k_gas_concentration, k_scattering_model, time_step); // Updating velocity according to gas collision.
            Ray ray(prev, particle.getCentre());

            // Check ray on degeneracy.
            if (!ray.is_degenerate())
            {
                // Check intersection of ray with mesh.
                auto intersection{_surfaceMeshAABBtree.any_intersection(ray)};
                if (intersection)
                {
                    // Getting triangle object.
                    auto triangle{boost::get<Triangle>(*intersection->second)};

                    // Check if some of sides of angles in the triangle <= 0 (check on degeneracy).
                    if (!triangle.is_degenerate())
                    {
                        // Finding matching triangle in the mesh.
                        auto matchedIt{std::ranges::find_if(_triangleMesh, [triangle](auto const &el)
                                                            { return triangle == std::get<1>(el); })};
                        if (matchedIt != _triangleMesh.cend())
                        {
                            size_t id{isRayIntersectTriangle(ray, *matchedIt)};
                            if (id != -1ul)
                            {
                                ++settledParticlesCounterMap[id];              // Filling map to detect how much particles settled on certain triangle.
                                _settledParticlesIds.insert(particle.getId()); // Remembering settled particle ID.
                            }
                        }
                    }
                }
            }
        }
    }
}
