#include <H5Cpp.h>
#include <filesystem>
#include <gtest/gtest.h>

#include "../include/DataHandling/HDF5Handler.hpp"

class HDF5HandlerTest : public ::testing::Test
{
protected:
    std::string filename{"test.hdf5"};
    HDF5Handler *handler{};

    void SetUp() override
    {
        if (std::filesystem::exists(filename))
            std::filesystem::remove(filename);
        handler = new HDF5Handler(filename);
    }

    void TearDown() override
    {
        delete handler;
        if (std::filesystem::exists(filename))
            std::filesystem::remove(filename);
    }
};

TEST_F(HDF5HandlerTest, FileCreation) { EXPECT_TRUE(std::filesystem::exists(filename)); }

TEST_F(HDF5HandlerTest, SaveAndReadMesh)
{
    // Create and save a mesh.
    MeshTriangleParamVector mesh;
    mesh.emplace_back(std::make_tuple(167ul, Triangle(Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)), 101.123f, 578'154));
    handler->saveMeshToHDF5(mesh);

    // Read back the mesh.
    MeshTriangleParamVector readMesh{handler->readMeshFromHDF5()};
    EXPECT_EQ(mesh.size(), readMesh.size());
    if (!readMesh.empty())
    {
        auto const &[id, triangle, area, count]{readMesh[0]};

        EXPECT_EQ(std::get<0>(mesh.at(0)), id);
        EXPECT_DOUBLE_EQ(std::get<2>(mesh.at(0)), area);
        EXPECT_EQ(std::get<3>(mesh.at(0)), count);
    }
}
