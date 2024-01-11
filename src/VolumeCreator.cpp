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
