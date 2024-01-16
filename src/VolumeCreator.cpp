#include <gmsh.h>

#include "../include/VolumeCreator.hpp"

Box::Box(double x_, double y_, double z_,
         double dx_, double dy_, double dz_) : x(x_), y(y_), z(z_),
                                               dx(dx_), dy(dy_), dz(dz_) {}

int Box::create() const
{
    return gmsh::model::occ::addBox(x, y, z, dx, dy, dz);
}

Sphere::Sphere(double x_, double y_, double z_, double r_) : x(x_), y(y_), z(z_), r(r_) {}

int Sphere::create() const
{
    return gmsh::model::occ::addSphere(x, y, z, r);
}

Cylinder::Cylinder(double x_, double y_, double z_,
                   double dx_, double dy_, double dz_,
                   double r_, double angle_, int tag_)
    : x(x_), y(y_), z(z_),
      dx(dx_), dy(dy_), dz(dz_),
      r(r_), angle(angle_), tag(tag_) {}

int Cylinder::create() const
{
    return gmsh::model::occ::addCylinder(x, y, z, dx, dy, dz, r, tag, angle);
}

Cone::Cone(double x_, double y_, double z_,
           double dx_, double dy_, double dz_,
           double r1_, double r2_, double angle_, int tag_)
    : x(x_), y(y_), z(z_),
      dx(dx_), dy(dy_), dz(dz_),
      r1(r1_), r2(r2_), angle(angle_), tag(tag_) {}

int Cone::create() const
{
    return gmsh::model::occ::addCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
}

void GMSHVolumeCreator::createBoxAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                         double x, double y, double z, double dx, double dy, double dz)
{
    VolumeCreator::createBox(x, y, z, dx, dy, dz);
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createSphereAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                            double x, double y, double z, double r)
{
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
