#include "../include/Utilities/CollisionTracker.hpp"
#include "../include/Utilities/ConfigParser.hpp"

void simulateMovement(ConfigParser const &configObj,
                      double gasConcentration,
                      std::string_view mshfilename,
                      std::string_view hdf5filename)
{
    MeshTriangleParamVector mesh;

    // Optimization 1: Artificial space for handling GMSH app.
    // To finilize GMSH as soon as possible.
    {
        GMSHVolumeCreator volumeCreator;
        mesh = volumeCreator.getMeshParams(mshfilename);

        if (mesh.empty())
        {
            ERRMSG(util::stringify("Something wrong with filling of the mesh. Mesh file is ", mshfilename, ". Exiting..."));
            std::exit(EXIT_FAILURE);
        }
    }
    auto pgs(createParticlesWithEnergy(configObj.getParticlesCount(),
                                       configObj.getProjective(),
                                       0, 0, 25,
                                       0, 0, 25,
                                       configObj.getEnergy(), configObj.getEnergy()));

    CollisionTracker ct(pgs, mesh, configObj, gasConcentration);
    auto counterMap{ct.trackCollisions(configObj.getNumThreads())};

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
        ERRMSG(util::stringify("File (", mshfilename, ") doesn't exist"));
        std::exit(EXIT_FAILURE);
    }
    if (time_step <= 0.0)
    {
        ERRMSG(util::stringify("Time step can't be less or equal 0"));
        std::exit(EXIT_FAILURE);
    }
    if (particles_count > 10'000'000)
    {
        ERRMSG(util::stringify("Particles count limited by 10'000'000.\nBut you entered ", particles_count));
        std::exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        ERRMSG(util::stringify("Usage: ", argv[0], " <config_file>"));
        return EXIT_FAILURE;
    }

    std::string configFilename(argv[1]);
    ConfigParser configParser(configFilename);

    std::string mshfilename(configParser.getMeshFilename()),
        hdf5filename(mshfilename.substr(0, mshfilename.find(".")) + ".hdf5");

    checkRestrictions(configParser.getTimeStep(), configParser.getParticlesCount(), configFilename);
    double gasConcentration(util::calculateConcentration(configFilename));

    if (gasConcentration < gasConcentrationMinimalValue)
        WARNINGMSG(util::stringify("Something wrong with the concentration of the gas. Its value is ", gasConcentration, ". Simulation might considerably slows down"));

    simulateMovement(configParser, gasConcentration, mshfilename, hdf5filename);

    return EXIT_SUCCESS;
}
