#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Geometry/Grid3D.hpp"
#include "../include/Particles/Particles.hpp"
#include "../include/Utilities/MatrixEquationSolver.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{100};

/**
 * @brief Checker for point inside the tetrahedron.
 * @param point `Point_3` from CGAL.
 * @param tetrahedron `Tetrahedron_3` from CGAL.
 * @return `true` if point within the tetrahedron, otherwise `false`.
 */
bool isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam)
{
    CGAL::Oriented_side oriented_side{std::get<1>(meshParam).oriented_side(particle.getCentre())};
    if (oriented_side == CGAL::ON_POSITIVE_SIDE)
        return true;
    else if (oriented_side == CGAL::ON_NEGATIVE_SIDE)
        return false;
    else
        // TODO: Correctly handle case when particle is on boundary of tetrahedron.
        return true;
}

int main(int argc, char *argv[])
{
#pragma region VolumeParticleTracking
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

    // 6. Start simulating and track particles in each time moment.
    std::map<size_t, ParticleVector> particleTracker; ///< Key - tetrahedron ID; Value - particles within tetrahedrons.
    double dt{0.1}, simtime{0.5};
    for (double t{}; t <= simtime; t += dt)
    {
        std::cout << std::format("\033[1;34mTime {}\n\033[0m", t);
        for (auto &pt : particles)
        {
            if (t != 0.0)
                pt.updatePosition(dt);

            auto meshParams{grid.getTetrahedronsByGridIndex(grid.getGridIndexByPosition(pt.getCentre()))};
            for (auto const &meshParam : meshParams)
                if (isParticleInsideTetrahedron(pt, meshParam))
                    particleTracker[std::get<0>(meshParam)].emplace_back(pt);
        }

        // 6.1_opt. Printing results.
        size_t count{};
        for (auto const &[tetrId, pts] : particleTracker)
        {
            count += pts.size();
            std::cout << std::format("Tetrahedron[{}]: ", tetrId);
            for (auto const &pt : pts)
                std::cout << pt.getId() << ' ';
            std::endl(std::cout);
        }
        std::cout << "Count of particles: " << count << '\n';
        particleTracker.clear();
    }
#pragma endregion

    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);
    {
        // 1. Assemblying global stiffness matrix from the mesh file.
        GSMatrixAssemblier assemblier(k_mesh_filename);

        // 2. Setting boundary conditions.
        std::map<int, double> boundaryConditions = {{0, 1.0}, {1, 1.0}, {12, 1.0}, {13, 1.0}};
        assemblier.setBoundaryConditions(boundaryConditions);
        assemblier.print(); // 2_opt. Printing the matrix.

        // 3. Getting the global stiffness matrix and its size to the variable.
        // Matrix is square, hence we can get only count of rows or cols.
        auto A{assemblier.getGlobalStiffnessMatrix()};
        auto size{assemblier.rows()};

        // 4. Creating solution vector, filling it with the random values, and applying boundary conditions.
        SolutionVector b(size);
        b.randomize();
        b.setBoundaryConditions(boundaryConditions);
        b.print(); // 4_opt. Printing the solution vector.

        // 5. Solve the equation Ax=b.
        MatrixEquationSolver solver(assemblier, b);
        solver.solveAndPrint();
    }

    Kokkos::finalize();
    return EXIT_SUCCESS;
}
