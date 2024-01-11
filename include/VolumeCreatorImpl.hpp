#ifndef VOLUMECREATORIMPL_HPP
#define VOLUMECREATORIMPL_HPP

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

template <SphereConcept T>
std::vector<int> VolumeCreator::createSpheres(std::span<T const> spheres)
{
    std::vector<int> dimTags;
    for (auto const &sphere : spheres)
        dimTags.emplace_back(VolumeCreator::createSphere(std::get<0>(sphere),
                                                         std::get<1>(sphere),
                                                         std::get<2>(sphere),
                                                         std::get<3>(sphere)));
    return dimTags;
}

#endif // !VOLUMECREATORIMPL_HPP
