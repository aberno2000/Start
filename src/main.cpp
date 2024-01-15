#include <map>
#include <numeric>

#include "../include/HDF5Handler.hpp"
#include "../include/Mesh.hpp"
#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"
#include "../include/VolumeCreator.hpp"

std::tuple<std::unordered_map<size_t, int>, SphereVector>
trackCollisions(ParticleGenericVector &pgs,
                TriangleMeshParamVector const &mesh,
                double dt, double total_time)
{
    std::unordered_map<size_t, int> m;
    SphereVector sv;

    for (double t{}; t <= total_time; t += dt)
    {
        pgs.erase(std::remove_if(pgs.begin(), pgs.end(), [dt, &m, &sv, mesh](auto &p)
                                 {
            PositionVector prevCentre(p.getPositionVector());
            p.updatePosition(dt);
            PositionVector nextCentre(p.getPositionVector());
            bool issettled{};
            for (auto const &triangle : mesh)
            {
                auto id{Mesh::intersectLineTriangle(prevCentre, nextCentre, triangle)};
                if (id != std::numeric_limits<size_t>::max())
                {
                    // Assume, that particle can settle only on one triangle of the mesh
                    std::cout << nextCentre << "\tr = " << p.getRadius() << '\n';
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

void simulateMovement(VolumeType vtype, size_t particles_count, double meshSize,
                      int meshDim, double dt, double simtime,
                      std::string_view outfile, [[maybe_unused]] int argc, [[maybe_unused]] char *argv[])
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
    TriangleMeshParamVector mesh{volumeCreator.getMeshParams(outfile.data())};

    // 3. Creating random particles
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count));

    // 4. Simulating movement - tracking collisions of the particles to walls
    auto tracked{trackCollisions(pgs, mesh, dt, simtime)};
    auto settledParticlesMap{std::get<0>(tracked)};
    auto settled{std::get<1>(tracked)};

    // 5. Viewing keys in ascending order
    switch (vtype)
    {
    case VolumeType::Box:
        std::cout << "\n\n\n*** Box ***\n";
        break;
    case VolumeType::Sphere:
        std::cout << "\n\n\n*** Sphere ***\n";
        break;
    case VolumeType::Cylinder:
        std::cout << "\n\n\n*** Cylinder ***\n";
        break;
    case VolumeType::Cone:
        std::cout << "\n\n\n*** Cone ***\n";
        break;
    default:
        break;
    }
    auto ordered{std::map<size_t, int>(settledParticlesMap.begin(), settledParticlesMap.end())};
    for (auto const &[id, count] : ordered)
        std::cout << std::format("Triangle[{}]: {}\n", id, count);
    std::cout << std::format("Total count: {}\nSettled count: {}\n", particles_count,
                             std::accumulate(settledParticlesMap.cbegin(), settledParticlesMap.cend(), 0,
                                             [](int count, auto const &nextEntry)
                                             { return count + nextEntry.second; }));

    // X. Creating settled particles in GMSH
    // volumeCreator.createSpheresAndMesh(settled, 1, 2, "results/particles.msh");
    volumeCreator.runGmsh(argc, argv);
}

int main(int argc, char *argv[])
{
    simulateMovement(VolumeType::Box, 50, 0.75, 2, 0.1, 2.0, "results/box.msh", argc, argv);
    simulateMovement(VolumeType::Sphere, 50, 0.6, 2, 0.01, 1.0, "results/sphere.msh", argc, argv);
    simulateMovement(VolumeType::Cylinder, 50, 0.4, 2, 0.2, 5.0, "results/cylinder.msh", argc, argv);
    simulateMovement(VolumeType::Cone, 50, 0.9, 2, 1.0, 10.0, "results/cone.msh", argc, argv);

    return EXIT_SUCCESS;
}
