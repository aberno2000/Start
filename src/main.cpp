#include "../include/ParticleTracker.hpp"

int main(int argc, char *argv[])
{
    // Initializing global MPI session and Kokkos.
    Teuchos::GlobalMPISession mpiSession(std::addressof(argc), std::addressof(argv));
    Kokkos::initialize(argc, argv);

    if (argc != 2)
    {
        ERRMSG(util::stringify("Usage: ", argv[0], " <config_file>"));
        return EXIT_FAILURE;
    }
    ParticleTracker particleTracker(argv[1]);
    particleTracker.startSimulation();

    Kokkos::finalize();
    return EXIT_SUCCESS;
}
