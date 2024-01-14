#include <map>
#include <numeric>

#include "../include/HDF5Handler.hpp"
#include "../include/Mesh.hpp"
#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"
#include "../include/VolumeCreator.hpp"

std::unordered_map<size_t, int> simulateMovement(ParticleGenericVector &pgs,
                                                 TriangleMeshParamVector const &mesh,
                                                 double dt, double total_time)
{
    std::unordered_map<size_t, int> m;
    for (double t{}; t <= total_time; t += dt)
    {
        pgs.erase(std::remove_if(pgs.begin(), pgs.end(), [dt, &m, mesh](auto &p)
                                 {
            PositionVector prevCentre(p.getPositionVector());
            p.updatePosition(dt);
            PositionVector nextCentre(p.getPositionVector());
            bool issettled{};
            for (auto const &triangle : mesh)
            {
                auto id{Mesh::intersectLineTriangle(prevCentre, nextCentre, triangle)};
                if (id != -1ul)
                {
                    // Assume, that particle can settle only on one triangle of the mesh
                    m[id]++;
                    issettled = true;
                    break;
                }
            }

            return issettled; }),
                  pgs.end());
    }
    return m;
}

int main()
{
    // 1. Generating cubic bounded volume in GMSH
    gmsh::initialize();
    VolumeCreator::createBox();
    Mesh::setMeshSize(0.75);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(2);

    // 2. Writing it to the .msh file
    gmsh::write("results/mesh.msh");
    TriangleMeshParamVector mesh{Mesh::getMeshParams("results/mesh.msh")};
    gmsh::finalize();

    // 3. Saving mesh to the HDF5
    HDF5Handler hdf5handler("results/mesh.hdf5");
    hdf5handler.saveMeshToHDF5(mesh);

    // 4. Creating random particles
    int particles_count{10'000};
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count));

    // 5. Simulating movement
    double dt{0.1}, simtime{10.0};
    auto settledParticles{simulateMovement(pgs, mesh, dt, simtime)};

    // 6. Viewing keys in ascending order
    std::cout << "Data from map\n";
    auto ordered{std::map<size_t, int>(settledParticles.begin(), settledParticles.end())};
    for (auto const &[id, count] : ordered)
        std::cout << std::format("Triangle[{}]: {}\n", id, count);
    std::cout << std::format("Total count: {}\nSettled count: {}\n", particles_count,
                             std::accumulate(settledParticles.cbegin(), settledParticles.cend(), 0,
                                             [](int count, auto const &nextEntry)
                                             { return count + nextEntry.second; }));

    // X. Updating counters of particles settlement
    hdf5handler.updateParticleCounters(settledParticles);
    mesh = hdf5handler.readMeshFromHDF5();

    return EXIT_SUCCESS;
}
