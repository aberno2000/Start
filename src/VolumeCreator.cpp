#include <gmsh.h>

#include "../include/Generators/VolumeCreator.hpp"

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

int VolumeCreator::createBox(double x, double y, double z, double dx, double dy, double dz)
{
    return gmsh::model::occ::addBox(x, y, z, dx, dy, dz);
}

int VolumeCreator::createSphere(double x, double y, double z, double r)
{
    return gmsh::model::occ::addSphere(x, y, z, r);
}

int VolumeCreator::createCylinder(double x, double y, double z,
                                  double dx, double dy, double dz,
                                  double r, int tag, double angle)
{
    return gmsh::model::occ::addCylinder(x, y, z, dx, dy, dz, r, tag, angle);
}

int VolumeCreator::createCone(double x, double y, double z,
                              double dx, double dy, double dz,
                              double r1, double r2, int tag, double angle)
{
    return gmsh::model::occ::addCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
}

std::vector<int> VolumeCreator::createSpheres(SphereVector spheres)
{
    std::vector<int> dimTags;
    for (auto const &sphere : spheres)
    {
        Point3 centre{std::get<0>(sphere)};
        dimTags.emplace_back(VolumeCreator::createSphere(CGAL_TO_DOUBLE(centre.x()),
                                                         CGAL_TO_DOUBLE(centre.y()),
                                                         CGAL_TO_DOUBLE(centre.z()),
                                                         std::get<1>(sphere)));
    }
    return dimTags;
}

GMSHVolumeCreator::GMSHandler::GMSHandler() { gmsh::initialize(); }
GMSHVolumeCreator::GMSHandler::~GMSHandler() { gmsh::finalize(); }

void GMSHVolumeCreator::gmshSynchronizer(double meshSize, double meshDim, std::string_view outputPath)
{
    Mesh::setMeshSize(meshSize);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(meshDim);
    gmsh::write(outputPath.data());
}

void GMSHVolumeCreator::createBoxAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                         double x, double y, double z, double dx, double dy, double dz)
{
    VolumeCreator::createBox(x, y, z, dx, dy, dz);
    gmshSynchronizer(meshSize, meshDim, outputPath);
}

void GMSHVolumeCreator::createSphereAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                            double x, double y, double z, double r)
{
    VolumeCreator::createSphere(x, y, z, r);
    gmshSynchronizer(meshSize, meshDim, outputPath);
}

void GMSHVolumeCreator::createSpheresAndMesh(SphereVector spheres, double meshSize,
                                             int meshDim, std::string_view outputPath)
{
    VolumeCreator::createSpheres(spheres);
    gmshSynchronizer(meshSize, meshDim, outputPath);
}

void GMSHVolumeCreator::createCylinderAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                              double x, double y, double z,
                                              double dx, double dy, double dz, double r,
                                              int tag, double angle)
{
    VolumeCreator::createCylinder(x, y, z, dx, dy, dz, r, tag, angle);
    gmshSynchronizer(meshSize, meshDim, outputPath);
}

void GMSHVolumeCreator::createConeAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                                          double x, double y, double z,
                                          double dx, double dy, double dz,
                                          double r1, double r2, int tag, double angle)
{
    VolumeCreator::createCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
    gmshSynchronizer(meshSize, meshDim, outputPath);
}

void GMSHVolumeCreator::createVolume(VolumeType vtype, double meshSize,
                                     double meshDim, std::string_view outputPath)
{
    switch (vtype)
    {
    case VolumeType::BoxType:
        createBoxAndMesh(meshSize, meshDim, outputPath);
        break;
    case VolumeType::SphereType:
        createSphereAndMesh(meshSize, meshDim, outputPath);
        break;
    case VolumeType::CylinderType:
        createCylinderAndMesh(meshSize, meshDim, outputPath);
        break;
    case VolumeType::ConeType:
        createConeAndMesh(meshSize, meshDim, outputPath);
        break;
    default:
        std::cerr << "\033[1;31mError:\033[0m\033[1m There is no such type\n";
        return;
    }
}

MeshParamVector GMSHVolumeCreator::getMeshParams(std::string_view msh_filename) { return Mesh::getMeshParams(msh_filename); }

TetrahedronMeshParamVector GMSHVolumeCreator::getTetrahedronMeshParams(std::string_view msh_filename) { return Mesh::getTetrahedronMeshParams(msh_filename); }

void GMSHVolumeCreator::runGmsh(int argc, char *argv[])
{
    // If there is no `-nopopup` argument - run the gmsh app
    if (std::find(argv, argv + argc, std::string("-nopopup")) == argv + argc)
        gmsh::fltk::run();
}
