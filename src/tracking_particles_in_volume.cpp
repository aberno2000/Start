#include "../include/FiniteElementMethod/MatrixEquationSolver.hpp"
#include "../include/Generators/VolumeCreator.hpp"
#include "../include/ParticleInCell/ParticleTracker.hpp"
#include "../include/Particles/Particles.hpp"

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
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 300, 300, 700);
    // vc.createSphereAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 500);
    // vc.createConeAndMesh(meshSize, 3, k_mesh_filename);

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
    tracker.printParticlesMap();
    tracker.printChargeDensityMap();

    /* Work with matrices. */
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);
    {
        // 1. Acquiring polynom order and desired calculation accuracy.
        int polynomOrder{}, desiredAccuracy;
        std::cout << "Enter polynom order to describe basis function: ";
        std::cin >> polynomOrder;
        std::cout << "Enter desired accuracy of calculations (this parameter influences the number of cubature points used for integrating over mesh elements when computing the stiffness matrix): ";
        std::cin >> desiredAccuracy;

        // 2. Assemblying global stiffness matrix from the mesh file.
        GSMatrixAssemblier assemblier(k_mesh_filename, polynomOrder, desiredAccuracy);

        // 3. Setting boundary conditions.
        std::map<int, double> boundaryConditions;
        for (size_t nodeId : Mesh::getTetrahedronMeshBoundaryNodes(k_mesh_filename)/* {2, 4, 6, 8, 28, 29, 30, 59, 60, 61, 50, 51, 52, 53, 54, 55,
                              215, 201, 206, 211, 203, 205, 207, 209, 204, 210, 214, 202, 208, 213, 212} */ // *Boundary conditions for box: 300x300x700, mesh size: 1
                              /* {33, 40, 30, 146, 119, 32, 41, 162, 125} */ // *Boundary conditions for sphere: R=500, mesh size: 1
                              /* {19, 20, 21, 22, 23, 24, 2, 90} */ // *Boundary conditions for default cone: mesh size: 1
                              )
            boundaryConditions[nodeId] = 0.0;
        for (int nodeId : {1, 3, 5, 7, 17, 18, 19, 39, 40, 41, 56, 57, 58, 62, 63, 64, 230,
                           216, 221, 226, 224, 218, 220, 222, 225, 229, 217, 228, 223, 219, 227} // *Boundary conditions for box: 300x300x700, mesh size: 1
                           /* {84, 78, 132, 79, 104, 103, 85} */ // *Boundary conditions for sphere: R=500, mesh size: 1
                           /* {1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 85, 86, 87, 88, 89} */) 
            boundaryConditions[nodeId] = 1.0;

        assemblier.setBoundaryConditions(boundaryConditions);
        assemblier.print(); // 3_opt. Printing the matrix.

        // 4. Getting the global stiffness matrix and its size to the variable.
        // Matrix is square, hence we can get only count of rows or cols.
        auto A{assemblier.getGlobalStiffnessMatrix()};
        auto size{assemblier.rows()};

        // 5. Creating solution vector, filling it with the random values, and applying boundary conditions.
        SolutionVector b(size, polynomOrder);
        b.clear();
        b.setBoundaryConditions(boundaryConditions);
        b.print(); // 4_opt. Printing the solution vector.

        // 6. Solve the equation Ax=b.
        MatrixEquationSolver solver(assemblier, b);
        solver.solveAndPrint();
        solver.printLHS();

        // 7. Gathering results from the solution of the equation Ax=b to the GMSH .pos file.
        solver.writeElectricPotentialsToPosFile();

        // 8. Making vectors of electrical field for all the tetrahedra in GMSH .pos file.
        solver.writeElectricFieldVectorsToPosFile();
    }
    Kokkos::finalize();

    return EXIT_SUCCESS;
}
