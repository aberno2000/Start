#include <gmsh.h>
#include <gtest/gtest.h>

#include "../include/Geometry/MathVector.hpp"
#include "../include/Geometry/Mesh.hpp"
#include "../include/Utilities/Utilities.hpp"

class MeshTest : public ::testing::Test
{
protected:
    static void SetUpTestSuite() { gmsh::initialize(); }
    static void TearDownTestSuite() { gmsh::finalize(); }

    void SetUp() override {}
    void TearDown() override {}
};

TEST_F(MeshTest, CalculateVolumeOfTetrahedron)
{
    Tetrahedron tetra(Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0), Point(0, 0, 1));
    double volume{calculateVolumeOfTetrahedron(tetra)};
    EXPECT_NEAR(volume, 1.0 / 6.0, 1e-6);
}

TEST_F(MeshTest, AABBTreeConstruction)
{
    MeshTriangleParamVector params;
    params.push_back(std::make_tuple(1, Triangle(Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)), 0.5, 0));
    auto aabb_tree = constructAABBTreeFromMeshParams(params);
    EXPECT_TRUE(aabb_tree.has_value());
}

TEST_F(MeshTest, RayIntersectsTriangle)
{
    Ray ray(Point(0, 0, 1), Point(0, 0, -1));
    size_t intersection{RayTriangleIntersection::isIntersectTriangle(ray, Triangle(Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)))};
    EXPECT_EQ(intersection, 1);
}

TEST_F(MeshTest, IntersectionPointImplementation)
{
    Ray ray(Point(0, 0, 1), Point(0, 0, -1));
    auto result{RayTriangleIntersection::getIntersectionPoint(ray, Triangle(Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0)))};
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, Point(0, 0, 0));
}

TEST_F(MeshTest, GetMeshParams)
{
    std::string filepath("TriangleTestMesh.msh");
    std::ifstream ifile(filepath);
    ASSERT_TRUE(ifile.good()) << "File not found or cannot be opened: " << filepath;

    auto meshParams{Mesh::getMeshParams(filepath)};
    ASSERT_FALSE(meshParams.empty()) << "Mesh parameters are empty, possibly due to parsing errors or empty file.";
}

TEST_F(MeshTest, GetTetrahedronMeshParams)
{
    std::string filepath("TetrahedronTestMesh.msh");
    std::ifstream ifile(filepath);
    ASSERT_TRUE(ifile.good()) << "File not found or cannot be opened: " << filepath;

    auto tetraMeshParams{Mesh::getTetrahedronMeshParams(filepath)};
    ASSERT_FALSE(tetraMeshParams.empty()) << "Tetrahedron mesh parameters are empty, check mesh file integrity or content.";
}

TEST_F(MeshTest, TotalVolumeFromTetrahedrons)
{
    std::string filepath("TetrahedronTestMesh.msh");
    std::ifstream ifile(filepath);
    ASSERT_TRUE(ifile.good()) << "File not found or cannot be opened: " << filepath;

    double totalVolume{Mesh::getVolumeFromTetrahedronMesh(filepath)};
    EXPECT_GT(totalVolume, 0) << "Calculated volume is non-positive, check tetrahedron definitions or calculations.";
}

TEST_F(MeshTest, MeshBoundaryNodes)
{
    std::string filepath("TetrahedronTestMesh.msh");
    std::ifstream ifile(filepath);
    ASSERT_TRUE(ifile.good()) << "File not found or cannot be opened: " << filepath;

    auto boundaryNodes{Mesh::getTetrahedronMeshBoundaryNodes(filepath)};
    EXPECT_FALSE(boundaryNodes.empty()) << "Boundary nodes list is empty, ensure boundary definitions are correct.";
}