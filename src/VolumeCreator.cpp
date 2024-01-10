#include <gmsh.h>

#include "../include/VolumeCreator.hpp"

int Box::create() const
{
    return gmsh::model::occ::addBox(x, y, z, dx, dy, dz);
}

int Sphere::create() const
{
    return gmsh::model::occ::addSphere(x, y, z, r);
}

int Cylinder::create() const
{
    return gmsh::model::occ::addCylinder(x, y, z, dx, dy, dz, r, tag, angle);
}

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
