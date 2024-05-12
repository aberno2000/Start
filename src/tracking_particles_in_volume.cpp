#include <algorithm>
#include <execution>

#include "../include/FiniteElementMethod/MatrixEquationSolver.hpp"
#include "../include/Generators/VolumeCreator.hpp"
#include "../include/ParticleInCell/ParticleInCellTracker.hpp"
#include "../include/Particles/Particles.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{1'000};

int main(int argc, char *argv[])
{
    // Initializing global MPI session and Kokkos.
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);

    // Creating particles.
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al,
                                                 0, 0, 0,
                                                 300, 300, 300,
                                                 -100, -100, -100,
                                                 100, 100, 100)};

    // Creating box in the GMSH application.
    GMSHVolumeCreator vc;
    double meshSize{};
    std::cout << "Enter box mesh size: ";
    std::cin >> meshSize;
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 300, 300, 700);

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
        double dt{0.1}, simtime{0.5};
        for (double t{}; t < simtime; t += dt)
        {
            std::cout << std::format("\033[1;34mTime {} s\n\033[0m", t);

            /* (Tetrahedron ID | Particles inside) */
            std::map<size_t, ParticleVector> PICtracker; // Map to managing in which tetrahedron how many and which particles are in the time moment `t`.

            /* (Tetrahedron ID | Charge density in coulumbs) */
            std::map<size_t, double> tetrahedronChargeDensityMap;

            /* (Node ID | Charge in coulumbs) */
            std::map<GlobalOrdinal, double> nodeChargeDensityMap;

            // For each time step managing movement of each particle.
            for (auto &particle : particles)
            {
                // Determine which tetrahedrons the particle may intersect based on its grid index.
                auto meshParams{grid.getTetrahedronsByGridIndex(grid.getGridIndexByPosition(particle.getCentre()))};
                for (auto const &meshParam : meshParams)
                    if (Mesh::isPointInsideTetrahedron(particle.getCentre(), meshParam))
                        PICtracker[std::get<0>(meshParam)].emplace_back(particle);

                // Updating particle position after filling `PICtracker`.
                particle.updatePosition(dt);
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

            // Gathering results from the solution of the equation Ax=b to the GMSH .pos file.
            solver.writeElectricPotentialsToPosFile();

            // Making vectors of electrical field for all the tetrahedra in GMSH .pos file.
            solver.writeElectricFieldVectorsToPosFile();

            // Next steps:
            // 1. EM-pushing particle with Boris Integrator.
            // 2. Updating velocity with the according scattering model: HS/VHS/VSS.
            // 3. Check on particle collision with surface - if so, remove it.
        }
    }
    Kokkos::finalize();
    return EXIT_SUCCESS;
}
