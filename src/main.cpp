#include <map>
#include <numeric>

#include "../include/HDF5Handler.hpp"
#include "../include/Mesh.hpp"
#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"
#include "../include/VolumeCreator.hpp"

std::tuple<std::unordered_map<size_t, int>, SphereVector>
trackCollisions(ParticleGenericVector &pgs, aabb::AABB const &bounding_volume,
                TriangleMeshParamVector const &mesh,
                double dt, double total_time)
{
    std::unordered_map<size_t, int> m;
    SphereVector sv;

    for (double t{}; t <= total_time; t += dt)
    {
        pgs.erase(std::remove_if(pgs.begin(), pgs.end(), [dt, &m, &sv, bounding_volume, mesh](auto &p)
                                 {
            PositionVector prevCentre(p.getPositionVector());
            p.updatePosition(dt);
            PositionVector nextCentre(p.getPositionVector());
            bool issettled{};

            if (!p.isOutOfBounds(bounding_volume)) return issettled;
            
            for (auto const &triangle : mesh)
            {
                auto id{Mesh::intersectLineTriangle(prevCentre, nextCentre, triangle)};
                if (id != std::numeric_limits<size_t>::max())
                {
                    // Assume, that particle can settle only on one triangle of the mesh
                    sv.emplace_back(std::make_tuple(nextCentre, p.getRadius()));
                    ++m[id];
                    issettled = true;
                    break;
                }
            }

            return issettled; }),
                  pgs.end());
    }
    return std::make_tuple(m, sv);
}

void simulateMovement(VolumeType vtype, size_t particles_count,
                      double meshSize, int meshDim, double dt, double simtime,
                      std::string_view outfile, std::string_view hdf5filename,
                      int argc, char *argv[])
{
    // 1. Generating cubic bounded volume in GMSH
    GMSHVolumeCreator volumeCreator;

    // 2. Choosing the volume type
    switch (vtype)
    {
    case VolumeType::Box:
        volumeCreator.createBoxAndMesh(meshSize, meshDim, outfile.data());
        break;
    case VolumeType::Sphere:
        volumeCreator.createSphereAndMesh(meshSize, meshDim, outfile.data());
        break;
    case VolumeType::Cylinder:
        volumeCreator.createCylinderAndMesh(meshSize, meshDim, outfile.data());
        break;
    case VolumeType::Cone:
        volumeCreator.createConeAndMesh(meshSize, meshDim, outfile.data());
        break;
    default:
        std::cerr << "There is no such type\n";
        return;
    }

    // 3. Getting mesh parameters from .msh file
    TriangleMeshParamVector mesh{volumeCreator.getMeshParams(outfile.data())};

    // 4. Creating random particles
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count));

    // 5. Simulating movement - tracking collisions of the particles to walls
    auto tracked{trackCollisions(pgs, volumeCreator.getBoundingVolume(), mesh, dt, simtime)};
    auto counterMap{std::get<0>(tracked)};
    auto settledParticles{std::get<1>(tracked)};

    // 6. Updating particle counters
    for (auto &triangle : mesh)
    {
        auto id{std::get<0>(triangle)};
        if (auto it{counterMap.find(id)}; it != counterMap.cend())
            std::get<5>(triangle) = it->second;
    }

    // 7. Saving mesh with updated counters to HDF5
    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};

    // 8. Creating settled particles in GMSH
    volumeCreator.createSpheresAndMesh(settledParticles, 1, 2, "results/particles.msh");
    volumeCreator.runGmsh(argc, argv);
}

int main(int argc, char *argv[])
{
    simulateMovement(VolumeType::Box, 1050, 0.75, 2, 0.1, 2.0, "results/box.msh", "results/box_mesh.hdf5", argc, argv);
    simulateMovement(VolumeType::Sphere, 555, 0.6, 2, 0.01, 1.0, "results/sphere.msh", "results/sphere_mesh.hdf5", argc, argv);
    simulateMovement(VolumeType::Cylinder, 475, 0.4, 2, 0.2, 5.0, "results/cylinder.msh", "results/cylinder_mesh.hdf5", argc, argv);
    simulateMovement(VolumeType::Cone, 2085, 0.9, 2, 1.0, 10.0, "results/cone.msh", "results/cone_mesh.hdf5", argc, argv);

    return EXIT_SUCCESS;
}
