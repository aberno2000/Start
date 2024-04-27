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
                                       configObj.getEnergy(),
                                       util::getParticleSourceCoordsAndDirection()));

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

    util::checkRestrictions(configParser.getTimeStep(), configParser.getParticlesCount(), configFilename);
    double gasConcentration(util::calculateConcentration(configFilename));

    if (gasConcentration < gasConcentrationMinimalValue)
        WARNINGMSG(util::stringify("Something wrong with the concentration of the gas. Its value is ", gasConcentration, ". Simulation might considerably slows down"));

    simulateMovement(configParser, gasConcentration, mshfilename, hdf5filename);

    return EXIT_SUCCESS;
}
