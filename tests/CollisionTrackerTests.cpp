#include <gtest/gtest.h>
#include <regex>

#include "../include/Utilities/CollisionTracker.hpp"

class CollisionTrackerTest : public ::testing::Test
{
protected:
    void SetUp() override {}
    void TearDown() override {}
};

std::vector<std::string> GetConfigFiles(std::string_view directory, std::regex const &pattern)
{
    std::vector<std::string> files;
    for (auto const &entry : std::filesystem::directory_iterator(directory))
        if (entry.is_regular_file() && std::regex_match(entry.path().filename().string(), pattern))
            files.emplace_back(entry.path().string());
    return files;
}

void TestHelperValidConfigs(std::string_view config_filename, std::string_view mesh_filename)
{
    MeshTriangleParamVector mesh;

    // Optimization 1: Artificial space for handling GMSH app.
    // To finilize GMSH as soon as possible.
    {
        GMSHVolumeCreator volumeCreator;
        EXPECT_NO_THROW(mesh = volumeCreator.getMeshParams(mesh_filename));

        if (mesh.empty())
        {
            ERRMSG(util::stringify("Something wrong with filling of the mesh. Mesh file is ", mesh_filename, ". Exiting..."));
            std::exit(EXIT_FAILURE);
        }
    }
    ConfigParser configObj(config_filename);
    auto particles(createParticlesWithVelocities(configObj.getParticlesCount(),
                                                 configObj.getProjective()));

    double gasConcentration(util::calculateConcentration(config_filename));
    if (gasConcentration < gasConcentrationMinimalValue)
        WARNINGMSG(util::stringify("Something wrong with the concentration of the gas. Its value is ", gasConcentration, ". Simulation might considerably slows down"));
    EXPECT_GT(gasConcentration, gasConcentrationMinimalValue) << ": config file: " << config_filename;

    CollisionTracker ct(particles, mesh, configObj, gasConcentration);
    auto counterMap{ct.trackCollisions(configObj.getNumThreads())};

    auto mapEnd{counterMap.end()};
    for (auto &triangle : mesh)
        if (auto it{counterMap.find(std::get<0>(triangle))}; it != mapEnd)
            std::get<3>(triangle) = it->second;

    std::string hdf5_filename("test_hdf5file_to_check_collision_tracker.hdf5");
    HDF5Handler hdf5handler(hdf5_filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};
    EXPECT_FALSE(updatedMesh.empty()) << ": Check HDF5 file: " << hdf5_filename;

    if (std::filesystem::exists(hdf5_filename))
        std::filesystem::remove(hdf5_filename);
}

TEST_F(CollisionTrackerTest, TrackCollisionsForValidConfigs)
{
    std::string dirToSearchFiles("../configs/");
    std::regex pattern(R"(config_valid_\d+\.json\.gtest)");

    auto configFiles{GetConfigFiles(dirToSearchFiles, pattern)};
    EXPECT_FALSE(configFiles.empty()) << "There is no config files in " << dirToSearchFiles << " directory";

    short experimentId{};
    for (auto const &configFile : configFiles)
    {
        if (experimentId < 2)
            TestHelperValidConfigs(configFile, "../meshes/BoxMeshTest.msh.gtest");
        if (experimentId < 4)
            TestHelperValidConfigs(configFile, "../meshes/ConeMeshTest.msh.gtest");
        if (experimentId < 8)
            TestHelperValidConfigs(configFile, "../meshes/CylinderMeshTest.msh.gtest");
        if (experimentId >= 8)
            TestHelperValidConfigs(configFile, "../meshes/SphereMeshTest.msh.gtest");

        ++experimentId;
    }
}

TEST_F(CollisionTrackerTest, GetConfigFilesForInvalid)
{
    std::string dirToSearchFiles("../configs/");
    std::regex pattern(R"(config_invalid_\d+\.json\.gtest)");

    auto configFiles{GetConfigFiles(dirToSearchFiles, pattern)};
    ASSERT_FALSE(configFiles.empty()) << "No invalid config files found.";

    for (auto const &configFile : configFiles)
    {
        ConfigParser configObj(configFile);
        ASSERT_NE(configObj.getStatusCode(), STATUS_OK) << "Invalid config file parsed without error: " << configFile;
    }
}
