#include "../include/Utilities/CollisionTracker.hpp"

void simulateMovement(size_t particles_count, double dt, double total_time,
                      std::string_view outfile, std::string_view hdf5filename)
{
    MeshParamVector mesh;

    // Artificial space for handling GMSH app
    {
        GMSHVolumeCreator volumeCreator;
        mesh = volumeCreator.getMeshParams(outfile);
    }
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count, -50, -50, -50,
                                                                             100, 100, 100, -50, -50, -50,
                                                                             50, 50, 50));

    CollisionTracker ct(pgs, mesh, dt, total_time);
    auto counterMap{ct.trackCollisions()};

    for (auto &triangle : mesh)
        if (auto it{counterMap.find(std::get<0>(triangle))}; it != counterMap.cend())
            std::get<3>(triangle) = it->second;

    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};
}

int main(int argc, char *argv[])
{
    if (argc != 5)
    {
        std::cerr << std::format("Usage: {} <particles_count> <time_step> <time_interval> <msh_filename>\n",
                                 argv[0]);
        return EXIT_FAILURE;
    }
    int particles_count{std::stoi(argv[1])};
    double time_step{std::stod(argv[2])},
        time_interval{std::stod(argv[3])};
    std::string mshfilename(argv[4]),
        hdf5filename(mshfilename.substr(0ul, mshfilename.find(".")) + ".hdf5");

    simulateMovement(particles_count, time_step, time_interval, mshfilename, hdf5filename);

    return EXIT_SUCCESS;
}
