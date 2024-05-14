#include "../include/Generators/VolumeCreator.hpp"
#include "../include/ParticleTracker.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{10'000};
static constexpr ParticleType k_projective{particle_types::Al};
static constexpr double k_time_step{0.1};
static constexpr double k_simtime{0.5};

int main(int argc, char *argv[])
{
    // Initializing global MPI session and Kokkos.
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);

    // Creating box in the GMSH application.
    {
        GMSHVolumeCreator vc;
        double meshSize{1};
        vc.createBoxAndMesh(meshSize, 3, k_mesh_filename, 0, 0, 0, 300, 300, 700);
    }

    // Getting edge size from user's input.
    double edgeSize{10};
    std::cout << "Enter cubic mesh size (size of the cube edge): ";
    // std::cin >> edgeSize;

    // Acquiring polynom order and desired calculation accuracy.
    short desiredAccuracy{3};
    std::cout << "Enter desired accuracy of calculations (this parameter influences the number of cubature points used for integrating over mesh elements when computing the stiffness matrix): ";
    // std::cin >> desiredAccuracy;

    ParticleTracker pt(k_mesh_filename);
    pt.startSimulation(k_projective, k_particles_count, edgeSize, desiredAccuracy, k_time_step, k_simtime);

    Kokkos::finalize();
    return EXIT_SUCCESS;
}
