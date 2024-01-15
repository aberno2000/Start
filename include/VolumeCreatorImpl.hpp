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
        PositionVector pos{std::get<0>(sphere)};
        dimTags.emplace_back(VolumeCreator::createSphere(pos.getX(),
                                                         pos.getY(),
                                                         pos.getZ(),
                                                         std::get<1>(sphere)));
    }
    return dimTags;
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

#endif // !VOLUMECREATORIMPL_HPP
