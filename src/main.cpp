#include "../include/Utilities/CollisionTracker.hpp"
#include "../include/Utilities/ConfigParser.hpp"

void simulateMovement(size_t particles_count, double dt, double total_time,
                      std::string_view outfile, std::string_view hdf5filename,
                      unsigned int num_threads = std::thread::hardware_concurrency())
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

    // Limitation to restrict start program with threads count > it has.
    num_threads = (num_threads > std::thread::hardware_concurrency())
                      ? std::thread::hardware_concurrency()
                      : num_threads;

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

void checkRestrictions(double time_step, size_t particles_count, std::string_view mshfilename)
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
        std::cerr << std::format("Error: Particles count limited by 10'000'000.\nBut you entered {}\n",
                                 particles_count);
        std::exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        std::cerr << std::format("Usage: {} <config_file> <mesh_filename.msh>\n", argv[0]);
        return EXIT_FAILURE;
    }

    std::string configFilename(argv[1]),
        mshfilename(argv[2]),
        hdf5filename(mshfilename.substr(0, mshfilename.find(".")) + ".hdf5");
    ConfigParser configParser(configFilename);
    checkRestrictions(configParser.getTimeStep(), configParser.getParticlesCount(), configFilename);
    simulateMovement(configParser.getParticlesCount(), configParser.getTimeStep(),
                     configParser.getSimulationTime(), mshfilename, hdf5filename,
                     configParser.getNumThreads());

    return EXIT_SUCCESS;
}
