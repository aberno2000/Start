#include "../include/Utilities/CollisionTracker.hpp"

void simulateMovement(size_t particles_count, double dt, double total_time,
                      std::string_view outfile, std::string_view hdf5filename,
                      size_t num_threads = std::thread::hardware_concurrency())
{
    MeshParamVector mesh;

    // Optimization 1: Artificial space for handling GMSH app.
    // To finilize GMSH as soon as possible.
    {
        GMSHVolumeCreator volumeCreator;
        mesh = volumeCreator.getMeshParams(outfile);
    }
    auto pgs(createParticlesWithVelocities(particles_count, ParticleType::Ar,
                                           -50, -50, -50,
                                           100, 100, 100, -50, -50, -50,
                                           50, 50, 50));

    CollisionTracker ct(pgs, mesh, dt, total_time);
    auto counterMap{ct.trackCollisions(num_threads)};

    auto mapEnd{counterMap.end()};
    for (auto &triangle : mesh)
        if (auto it{counterMap.find(std::get<0>(triangle))}; it != mapEnd)
            std::get<3>(triangle) = it->second;

    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};
}

void checkRestrictions(double time_step, int particles_count, std::string_view mshfilename)
{
    if (not util::exists(mshfilename))
    {
        std::cerr << std::format("Error: File {} doesn't exist\n", mshfilename);
        std::exit(EXIT_FAILURE);
    }
    if (time_step == 0.0)
    {
        std::cerr << "Error: Time step can't be 0.\n";
        std::exit(EXIT_FAILURE);
    }
    if (particles_count > 10'000'000)
    {
        std::cerr << "Error: Particles count limited by 10'000'000.\n";
        std::exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[])
{
    if (argc != 5 && argc != 6)
    {
        std::cerr << std::format("Usage: {} <particles_count> <time_step> <time_interval> <msh_filename> [<num_threads>]\n",
                                 argv[0]);
        return EXIT_FAILURE;
    }
    int particles_count{std::stoi(argv[1])};
    double time_step{std::stod(argv[2])},
        time_interval{std::stod(argv[3])};
    std::string mshfilename(argv[4]),
        hdf5filename(mshfilename.substr(0ul, mshfilename.find(".")) + ".hdf5");

    checkRestrictions(time_step, particles_count, mshfilename);

    if (argc == 6)
    {
        size_t num_threads{std::stoul(argv[5])};
        simulateMovement(particles_count, time_step, time_interval, mshfilename, hdf5filename, num_threads);
    }
    else if (argc < 6)
        simulateMovement(particles_count, time_step, time_interval, mshfilename, hdf5filename);

    return EXIT_SUCCESS;
}
