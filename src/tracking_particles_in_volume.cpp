#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Particles/Particles.hpp"
#include "../include/Utilities/MatrixEquationSolver.hpp"
#include "../include/Utilities/ParticleTracker.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{100};

int main(int argc, char *argv[])
{
    // 1. Creating particles.
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al)};

    // 2. Creating box in the GMSH application.
    GMSHVolumeCreator vc;
    double meshSize{};
    std::cout << "Enter box mesh size: ";
    std::cin >> meshSize;
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 100, 100, 300);

    // 3. Filling the tetrahedron mesh.
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};

    // 4. Getting edge size from user's input.
    double edgeSize{};
    std::cout << "Enter 2nd mesh size (size of the cube edge): ";
    std::cin >> edgeSize;

    // 5. Creating grid.
    Grid3D grid(tetrahedronMesh, edgeSize);

    // 6. Tracking particles inside the tetrahedrons.
    double dt{0.1}, simtime{0.5};
    ParticleTracker tracker(particles, grid, dt, simtime);
    tracker.trackParticles();

    /* Work with matrices. */
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);
    {
        // 1. Assemblying global stiffness matrix from the mesh file.
        GSMatrixAssemblier assemblier(k_mesh_filename);

        // 2. Setting boundary conditions.
        std::map<int, double> boundaryConditions;
        for (int nodeId : {1, 3, 5, 7, 36})
            boundaryConditions[nodeId] = 1.0;
        for (int nodeId : {0, 2, 4, 6, 37})
            boundaryConditions[nodeId] = 0.0;

        assemblier.setBoundaryConditions(boundaryConditions);
        assemblier.print(); // 2_opt. Printing the matrix.

        // 3. Getting the global stiffness matrix and its size to the variable.
        // Matrix is square, hence we can get only count of rows or cols.
        auto A{assemblier.getGlobalStiffnessMatrix()};
        auto size{assemblier.rows()};

        // 4. Creating solution vector, filling it with the random values, and applying boundary conditions.
        SolutionVector b(size);
        b.clear();
        b.setBoundaryConditions(boundaryConditions);
        b.print(); // 4_opt. Printing the solution vector.

        // 5. Solve the equation Ax=b.
        MatrixEquationSolver solver(assemblier, b);
        solver.solveAndPrint();
        solver.printLHS();

        /* Colorizing results from the global stiffness matrix. */
        std::ofstream posFile("scalarField.pos");
        posFile << "View \"Scalar Field\" {\n";
        auto tetrahedronMap{Mesh::getTetrahedronNodesMap(k_mesh_filename)};
        auto nodes{Mesh::getTetrahedronNodeCoordinates(k_mesh_filename)};
        for (auto const &[tetrahedronID, nodeIDs] : tetrahedronMap)
        {
            Tetrahedron tetrahedron;
            for (auto const &[tetraID, tetra, volume] : tetrahedronMesh)
                if (tetrahedronID == tetraID)
                {
                    tetrahedron = tetra;
                    break;
                }

            posFile << "ST(";
            for (size_t i{}; i < nodeIDs.size(); ++i)
            {
                // Fetch coordinates for each node in the tetrahedron.
                auto nodeID{nodeIDs[i] - 1};
                if (nodes.find(nodeID) != nodes.end())
                {
                    auto const &coords{nodes[nodeID]};
                    posFile << coords[0] << ", " << coords[1] << ", " << coords[2];
                    if (i < nodeIDs.size() - 1)
                        posFile << ", ";
                }
            }
            posFile << "){";
            for (size_t i{}; i < nodeIDs.size(); ++i)
            {
                auto nodeID{nodeIDs[i] - 1};
                auto value{assemblier.getScalarFieldValue(nodeID)};
                posFile << value;
                if (i < nodeIDs.size() - 1)
                    posFile << ", ";
            }
            posFile << "};\n";
        }
        posFile << "};\n";
        posFile.close();
        LOGMSG("File 'scalarField.pos' was successfully created");
    }

    Kokkos::finalize();
    return EXIT_SUCCESS;
}
