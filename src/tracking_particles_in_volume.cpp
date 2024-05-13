#include <algorithm>
#include <execution>

#include "../include/FiniteElementMethod/MatrixEquationSolver.hpp"
#include "../include/Generators/VolumeCreator.hpp"
#include "../include/ParticleInCell/ParticleInCellTracker.hpp"
#include "../include/Particles/Particles.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{1'000};
static constexpr ParticleType k_projective{particle_types::Al};
static constexpr ParticleType k_gas{particle_types::Ar};
static constexpr double k_gas_concentration{10e26};
static constexpr std::string_view k_scattering_model{"HS"};
static constexpr double k_time_step{0.1};
static constexpr double k_simtime{0.5};

int main(int argc, char *argv[])
{
    // Initializing global MPI session and Kokkos.
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);

    // Creating particles.
    auto particles{createParticlesWithVelocities(k_particles_count, k_projective,
                                                 0, 0, 0,
                                                 300, 300, 300,
                                                 -100, -100, -100,
                                                 100, 100, 1000)};

    // Creating box in the GMSH application.
    GMSHVolumeCreator vc;
    double meshSize{};
    std::cout << "Enter box mesh size: ";
    std::cin >> meshSize;
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 300, 300, 700);

    // Initializing triangle mesh and AABB tree for it.
    auto triangleMesh{vc.getMeshParams(k_mesh_filename)};
    if (triangleMesh.empty())
    {
        ERRMSG("Can't construct AABB for triangle mesh -> mesh is empty");
        return EXIT_FAILURE;
    }

    TriangleVector triangles;
    for (auto const &meshParam : triangleMesh)
    {
        auto const &triangle{std::get<1>(meshParam)};
        if (!triangle.is_degenerate())
            triangles.emplace_back(triangle);
    }

    if (triangles.empty())
    {
        ERRMSG("Can't create AABB for triangle mesh -> triangles from the mesh are invalid (all degenerate)");
        return EXIT_FAILURE;
    }
    AABB_Tree_Triangle tree(std::cbegin(triangles), std::cend(triangles));
    size_t totalParticlesCount{particles.size()}, deletedParticlesCounter{};

    // Filling the tetrahedron mesh and node tetrahedron map.
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};
    auto nodeTetrahedronMap{Mesh::getNodeTetrahedronsMap(k_mesh_filename)};

    // Getting edge size from user's input.
    double edgeSize{};
    std::cout << "Enter 2nd mesh size (size of the cube edge): ";
    std::cin >> edgeSize;

    // Creating grid.
    Grid3D grid(tetrahedronMesh, edgeSize);

    // Acquiring polynom order and desired calculation accuracy.
    int polynomOrder{}, desiredAccuracy;
    std::cout << "Enter polynom order to describe basis function: ";
    std::cin >> polynomOrder;
    std::cout << "Enter desired accuracy of calculations (this parameter influences the number of cubature points used for integrating over mesh elements when computing the stiffness matrix): ";
    std::cin >> desiredAccuracy;

    {
        // Assemblying global stiffness matrix from the mesh file.
        GSMatrixAssemblier assemblier(k_mesh_filename, polynomOrder, desiredAccuracy);

        // Setting boundary conditions.
        std::map<GlobalOrdinal, double> boundaryConditions;
        for (size_t nodeId : Mesh::getTetrahedronMeshBoundaryNodes(k_mesh_filename) /* {2, 4, 6, 8, 28, 29, 30, 59, 60, 61, 50, 51, 52, 53, 54, 55,
                               215, 201, 206, 211, 203, 205, 207, 209, 204, 210, 214, 202, 208, 213, 212} */
        )
            boundaryConditions[nodeId] = 0.0;
        // *Boundary conditions for box: 300x300x700, mesh size: 1
        for (GlobalOrdinal nodeId : {1, 3, 5, 7, 17, 18, 19, 39, 40, 41, 56, 57, 58, 62, 63, 64, 230,
                                     216, 221, 226, 224, 218, 220, 222, 225, 229, 217, 228, 223, 219, 227})
            boundaryConditions[nodeId] = 1.0;

        assemblier.setBoundaryConditions(boundaryConditions);
        assemblier.print(); // 3_opt. Printing the matrix.

        // Getting the global stiffness matrix and its size to the variable.
        // Matrix is square, hence we can get only count of rows or cols.
        auto A{assemblier.getGlobalStiffnessMatrix()};
        auto size{assemblier.rows()};

        // Tracking particles inside the tetrahedrons.
        for (double t{}; t < k_simtime; t += k_time_step)
        {
            std::cout << std::format("\033[1;34mTime {} s\n\033[0m", t);

            /* (Tetrahedron ID | Particles inside) */
            std::map<size_t, ParticleVector> PICtracker; // Map to managing in which tetrahedron how many and which particles are in the time moment `t`.

            /* (Tetrahedron ID | Charge density in coulumbs) */
            std::map<size_t, double> tetrahedronChargeDensityMap;

            /* (Node ID | Charge in coulumbs) */
            std::map<GlobalOrdinal, double> nodeChargeDensityMap;

            /* (Triangle ID | Counter of settled particle in this triangle) */
            std::map<size_t, int> settledParticlesMap;

            // For each time step managing movement of each particle.
            for (auto &particle : particles)
            {
                // Determine which tetrahedrons the particle may intersect based on its grid index.
                auto meshParams{grid.getTetrahedronsByGridIndex(grid.getGridIndexByPosition(particle.getCentre()))};
                for (auto const &meshParam : meshParams)
                    if (Mesh::isPointInsideTetrahedron(particle.getCentre(), meshParam))
                        PICtracker[std::get<0>(meshParam)].emplace_back(particle);
            }

            // Calculating charge density in each of the tetrahedron using `PICtracker`.
            for (auto const &[tetrId, particlesInside] : PICtracker)
                tetrahedronChargeDensityMap.insert({tetrId,
                                                    (std::accumulate(particlesInside.cbegin(), particlesInside.cend(), 0.0, [](double sum, Particle const &particle)
                                                                     { return sum + particle.getCharge(); })) /
                                                        (std::get<2>(grid.getTetrahedronMeshParamById(tetrId)) * 1e-9)}); // mm³ to m³.

            std::cout << "Charge density in tetrahedrons:\n";
            for (auto const &[tetrId, tetrDensity] : tetrahedronChargeDensityMap)
                std::cout << std::format("Tetrahedron[{}]: {} C/m³\n", tetrId, tetrDensity);

            // Go around each node and aggregate data from adjacent tetrahedra.
            for (auto const &[nodeId, adjecentTetrahedrons] : nodeTetrahedronMap)
            {
                double totalCharge{}, totalVolume{};

                // Sum up the charge and volume for all tetrahedra of a given node.
                for (auto const &tetrId : adjecentTetrahedrons)
                {
                    if (tetrahedronChargeDensityMap.find(tetrId) != tetrahedronChargeDensityMap.end())
                    {
                        double tetrahedronChargeDensity{tetrahedronChargeDensityMap.at(tetrId)},
                            tetrahedronVolume{std::get<2>(grid.getTetrahedronMeshParamById(tetrId)) * 1e-9}; // mm³ в m³.

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
            SolutionVector b(size, polynomOrder);
            b.clear();
            if (t == 0.0)
                b.setBoundaryConditions(boundaryConditions);
            else
            {
                for (auto const &[nodeId, nodeChargeDensity] : boundaryConditions)
                    boundaryConditions[nodeId] = nodeChargeDensity;
                b.setBoundaryConditions(boundaryConditions);
            }
            b.print(); // 4_opt. Printing the solution vector.

            // Solve the equation Ax=b.
            MatrixEquationSolver solver(assemblier, b);
            solver.solveAndPrint();
            solver.printLHS();

            // Writing to files just ones.
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
            auto particlesIter{particles.begin()};
            while (particlesIter != particles.cend())
            {
                Particle &p{*particlesIter};

                // Finding tetrahedron that containing this particle.
                size_t containingTetrahedron{};
                for (auto const &[tetraId, particlesInside] : PICtracker)
                {
                    auto it{
                        std::ranges::find_if(particlesInside, [&p](Particle const &storedParticle)
                                             { return p.getId() == storedParticle.getId(); })};
                    if (it != particlesInside.cend())
                    {
                        containingTetrahedron = tetraId;
                        break; // If particle was found inside certain tetrahedron - breaking down the loop.
                    }
                }

                // Updating velocity according to the EM-field.
                if (electricFieldMap.find(containingTetrahedron) != electricFieldMap.cend())
                    p.electroMagneticPush(magneticInduction, electricFieldMap.at(containingTetrahedron), k_time_step);

                // Updating positions for all the particles.
                Point prev(p.getCentre()); // Saving previous particle position before updating the position.
                p.updatePosition(k_time_step);

                /* Gas collision part. */
                p.colide(k_gas, k_gas_concentration, k_scattering_model, k_time_step); // Updating velocity according to gas collision.
                Ray ray(prev, p.getCentre());

                // Check ray on degeneracy.
                if (!ray.is_degenerate())
                {
                    // Check intersection of ray with mesh.
                    auto intersection{tree.first_intersection(ray)};
                    if (intersection)
                    {
                        // Getting triangle object.
                        auto triangle{boost::get<Triangle>(*intersection->second)};

                        // Check if some of sides of angles in the triangle <= 0 (check on degeneracy).
                        if (!triangle.is_degenerate())
                        {
                            // Finding matching triangle in the mesh.
                            auto matchedIt{std::ranges::find_if(triangleMesh, [triangle](auto const &el)
                                                                { return triangle == std::get<1>(el); })};
                            if (matchedIt != triangleMesh.cend())
                            {
                                // Filling map to detect how much particles settled on certain triangle.
                                size_t id{Mesh::isRayIntersectTriangle(ray, *matchedIt)};
                                if (id != -1ul)
                                {
                                    ++settledParticlesMap[id];

                                    // Deleting settled particle.
                                    particlesIter = particles.erase(particlesIter);
                                    ++deletedParticlesCounter;
                                    continue; // Skip the increment step.
                                }
                            }
                        }
                    }
                }
                ++particlesIter; // Moving to the next particle.
            }
        }
    }
    Kokkos::finalize();
    std::cout << std::format("Total particles count: {}\nDeleted particles count: {}\nRemains: {}\n", totalParticlesCount, deletedParticlesCounter, particles.size());
    return EXIT_SUCCESS;
}
