#include <gmsh.h>
#include <gtest/gtest.h>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Generators/VolumeCreator.hpp"

SphereVector generateRandomSpheres(int count)
{
    SphereVector spheres;
    RealNumberGenerator rng;

    for (int i{}; i < count; ++i)
    {
        spheres.emplace_back(std::make_tuple(Point(rng(-100.0, 100.0),
                                                   rng(-100.0, 100.0),
                                                   rng(-100.0, 100.0)),
                                             rng(0, 100.0)));
    }
    return spheres;
}

class GeometryCreationTest : public ::testing::Test
{
protected:
    static void SetUpTestSuite()
    {
        gmsh::initialize();
        gmsh::model::add("GeometryCreation");
    }

    static void TearDownTestSuite() { gmsh::finalize(); }
};

TEST_F(GeometryCreationTest, BoxCreating) { EXPECT_EQ(VolumeCreator::createBox(10, 10, 10, 10, 20, 30), 1); }

TEST_F(GeometryCreationTest, SphereCreating) { EXPECT_EQ(VolumeCreator::createSphere(5, 5, 5, 5), 2); }

TEST_F(GeometryCreationTest, CylinderCreating) { EXPECT_EQ(VolumeCreator::createCylinder(0, 0, 0, 10, 20, 30, 5), 3); }

TEST_F(GeometryCreationTest, ConeCreating) { EXPECT_EQ(VolumeCreator::createCone(25, 25, 25, 10, 20, 30, 5, 10), 4); }

TEST_F(GeometryCreationTest, SpheresCreating)
{
    auto sphereTags{VolumeCreator::createSpheres(generateRandomSpheres(100))};
    int expectedTag{5};
    for (int tag : sphereTags)
        EXPECT_EQ(tag, expectedTag++);
}

TEST_F(GeometryCreationTest, RandomSpheresCreating)
{
    for (int i{}; i < 100; ++i)
    {
        auto spheres{generateRandomSpheres(10)};
        auto tags{VolumeCreator::createSpheres(spheres)};
        for (int tag : tags)
            EXPECT_GE(tag, 0);
    }
}
