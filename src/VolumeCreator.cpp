#include <gmsh.h>

#include "../include/VolumeCreator.hpp"

Box::Box(double x_, double y_, double z_,
         double dx_, double dy_, double dz_) : x(x_), y(y_), z(z_),
                                               dx(dx_), dy(dy_), dz(dz_),
                                               m_bounding_box({x, y, z}, {dx, dy, dz}) {}

int Box::create() const
{
    return gmsh::model::occ::addBox(x, y, z, dx, dy, dz);
}

Sphere::Sphere(double x_, double y_, double z_, double r_) : x(x_), y(y_), z(z_), r(r_),
                                                             m_bounding_box({x - r, y - r, z - r},
                                                                            {x + r, y + r, z + r}) {}

int Sphere::create() const
{
    return gmsh::model::occ::addSphere(x, y, z, r);
}

Cylinder::Cylinder(double x_, double y_, double z_,
                   double dx_, double dy_, double dz_,
                   double r_, double angle_, int tag_)
    : x(x_), y(y_), z(z_),
      dx(dx_), dy(dy_), dz(dz_),
      r(r_), angle(angle_), tag(tag_)
{
    // TODO: Correct bounding box
    m_bounding_box = aabb::AABB({x - r, y - r, z - r}, {dx + r, dy + r, dz + r});
}

int Cylinder::create() const
{
    return gmsh::model::occ::addCylinder(x, y, z, dx, dy, dz, r, tag, angle);
}

Cone::Cone(double x_, double y_, double z_,
           double dx_, double dy_, double dz_,
           double r1_, double r2_, double angle_, int tag_)
    : x(x_), y(y_), z(z_),
      dx(dx_), dy(dy_), dz(dz_),
      r1(r1_), r2(r2_), angle(angle_), tag(tag_)
{
    double rmin{std::min(r1, r2)}, rmax{std::max(r1, r2)};
    m_bounding_box = aabb::AABB({x - rmin, y - rmin, z - rmin}, {dx + rmax, dy + rmax, dz + rmax});
}

int Cone::create() const
{
    return gmsh::model::occ::addCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
}

void GMSHVolumeCreator::createBoxAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                         double x, double y, double z, double dx, double dy, double dz)
{
    m_bounding_volume = Box(x, y, z, dx, dy, dz).getBoundingBox();
    VolumeCreator::createBox(x, y, z, dx, dy, dz);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createSphereAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                            double x, double y, double z, double r)
{
    m_bounding_volume = Sphere(x, y, z, r).getBoundingBox();
    VolumeCreator::createSphere(x, y, z, r);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createSpheresAndMesh(SphereSpan spheres, double meshSize,
                                             int meshDim, std::string_view outputPath)
{
    VolumeCreator::createSpheres(spheres);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createCylinderAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                              double x, double y, double z,
                                              double dx, double dy, double dz, double r,
                                              int tag, double angle)
{
    m_bounding_volume = Cylinder(x, y, z, dx, dy, dz, r, angle, tag).getBoundingBox();
    VolumeCreator::createCylinder(x, y, z, dx, dy, dz, r, tag, angle);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createConeAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                          double x, double y, double z,
                                          double dx, double dy, double dz,
                                          double r1, double r2, int tag, double angle)
{
    m_bounding_volume = Cone(x, y, z, dx, dy, dz, r1, r2, angle, tag).getBoundingBox();

    VolumeCreator::createCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

TriangleMeshParamVector GMSHVolumeCreator::getMeshParams(std::string_view filePath) { return Mesh::getMeshParams(filePath); }

void GMSHVolumeCreator::runGmsh(int argc, char *argv[])
{
    // If there is no `-nopopup` argument - run the gmsh app
    if (std::find(argv, argv + argc, std::string("-nopopup")) == argv + argc)
        gmsh::fltk::run();
}

void GMSHVolumeCreator::createBoundingBoxOfLastObject(double meshSize, int meshDim, std::string_view outputPath)
{
    createBoxAndMesh(meshSize, meshDim, outputPath,
                     m_bounding_volume.lowerBound.at(0),
                     m_bounding_volume.lowerBound.at(1),
                     m_bounding_volume.lowerBound.at(2),
                     m_bounding_volume.upperBound.at(0),
                     m_bounding_volume.upperBound.at(1),
                     m_bounding_volume.upperBound.at(2));
}
