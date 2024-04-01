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
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename);

    // 3. Filling the tetrahedron mesh
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};

    // 4. Getting edge size from user.
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
        std::map<int, double> boundaryConditions = {
            {0, 1.0}, {2, 1.0}, {4, 1.0}, {6, 1.0}, {12, 1.0}, // Upper part of the cube.
            {1, 0.0}, {3, 0.0}, {5, 0.0}, {7, 0.0}, {13, 0.0}  // Lower part of the cube.
        };
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
    }

    Kokkos::finalize();
    return EXIT_SUCCESS;
}
