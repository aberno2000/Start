#ifndef VOLUMECREATORIMPL_HPP
#define VOLUMECREATORIMPL_HPP

inline int VolumeCreator::createBox(double x, double y, double z, double dx, double dy, double dz)
{
    return gmsh::model::occ::addBox(x, y, z, dx, dy, dz);
}

inline int VolumeCreator::createSphere(double x, double y, double z, double r)
{
    return gmsh::model::occ::addSphere(x, y, z, r);
}

inline int VolumeCreator::createCylinder(double x, double y, double z,
                                         double dx, double dy, double dz,
                                         double r, int tag, double angle)
{
    return gmsh::model::occ::addCylinder(x, y, z, dx, dy, dz, r, tag, angle);
}

inline int VolumeCreator::createCone(double x, double y, double z,
                                     double dx, double dy, double dz,
                                     double r1, double r2, int tag, double angle)
{
    return gmsh::model::occ::addCone(x, y, z, dx, dy, dz, r1, r2, tag, angle);
}

inline std::vector<int> VolumeCreator::createSpheres(SphereSpan spheres)
{
    std::vector<int> dimTags;
    for (auto const &sphere : spheres)
    {
        PointD centre{std::get<0>(sphere)};
        dimTags.emplace_back(VolumeCreator::createSphere(centre.x,
                                                         centre.y,
                                                         centre.z,
                                                         std::get<1>(sphere)));
    }
    return dimTags;
}

#endif // !VOLUMECREATORIMPL_HPP
