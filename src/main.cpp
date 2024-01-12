#include <fstream>

#include "../include/HDF5Handler.hpp"
#include "../include/Mesh.hpp"
#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"
#include "../include/VolumeCreator.hpp"

void writeInFile(std::span<ParticleGeneric const> particles, std::string_view filename)
{
    std::ofstream ofs(std::string(filename).c_str());
    if (!ofs.is_open())
        return;

    for (auto const &particle : particles)
        ofs << std::format("{} {} {} {} {} {} {}\n",
                           particle.getX(), particle.getY(), particle.getZ(),
                           particle.getVx(), particle.getVy(), particle.getVz(),
                           particle.getRadius());
    ofs.close();
}

ParticleGenericVector createParticles(size_t count)
{
    RealNumberGenerator rng;
    ParticleGenericVector particles(count);

    for (size_t i{}; i < count; ++i)
        particles[i] = ParticleGeneric(rng.get_double(10, 100),
                                       rng.get_double(10, 100),
                                       rng.get_double(10, 100),
                                       rng.get_double(0, 5),
                                       rng.get_double(0, 5),
                                       rng.get_double(0, 5),
                                       rng.get_double(0, 2));
    return particles;
}

ParticleVectorSimple truncateParticlesToXYZR(ParticleGenericVector particles)
{
    ParticleVectorSimple filtered;
    for (auto const &particle : particles)
        filtered.push_back({PositionVector{particle.getX(), particle.getY(), particle.getZ()},
                            particle.getRadius()});
    return filtered;
}

ParticleGenericVector simulateMovement(ParticleGenericVector &pgs,
                                       aabb::AABB const &bounding_volume,
                                       double dt, double total_time)
{
    ParticleGenericVector settled;
    for (double t{}; t <= total_time; t += dt)
    {
        pgs.erase(std::remove_if(pgs.begin(), pgs.end(), [dt, bounding_volume, &settled](auto &p)
                                 {
            p.updatePosition(dt);
            bool issettled{p.isOutOfBounds(bounding_volume)};
            if (issettled)
                settled.emplace_back(p);
            return issettled; }));
    }
    return settled;
}

int main(int argc, char *argv[])
{
    gmsh::initialize();
    aabb::AABB bounding_box({0, 0, 0}, {100, 100, 100});

    int particles_count{100'000};
    ParticleGenericVector pgs(createParticles(particles_count)); // 1'000'000 for Intel(R) Core(TM) i5-5300U CPU @ 2.30GHz
                                                                 // is harmful if synchronize models in gmsh

    VolumeCreator::createBox();
    Mesh::setMeshSize(0.75);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(2);

    auto particles{truncateParticlesToXYZR(pgs)};
    VolumeCreator::createSpheres(std::span<ParticleSimple const>(particles.data(), particles.size()));
    // gmsh::model::occ::synchronize();

    gmsh::write("results/mesh.msh");
    TriangleMeshParamVector mesh{Mesh::getMeshParams("results/mesh.msh")};
    HDF5Handler hdf5handler("results/mesh.hdf5");
    hdf5handler.saveMeshToHDF5(mesh);

    double simtime{1.0}, dt{0.1};
    ParticleGenericVector settled{simulateMovement(pgs, bounding_box, dt, simtime)};
    std::unordered_map<long unsigned, int> triangleCounters;
    for (auto const &particle : settled)
    {
        for (auto const &triangle : mesh)
        {
            if (int settledID{particle.isParticleInsideTriangle(triangle)}; settledID != -1)
            {
                // Assume, that particle can settle only on one triangle of the mesh
                triangleCounters[settledID]++;
                break;
            }
        }
    }
    hdf5handler.updateParticleCounters(triangleCounters);
    TriangleMeshParamVector meshForSettled(hdf5handler.readMeshFromHDF5(std::get<0>(mesh[0])));
    int totalSettledCount{};
    for (auto const &triangle : meshForSettled)
        if (std::get<5>(triangle) > 0)
        {
            totalSettledCount += std::get<5>(triangle);
            std::cout << std::format("{} particles settled on the triangle[{}]\n", std::get<5>(triangle),
                                     std::get<0>(triangle));
        }
    std::cout << std::format("Count of particles: {}\nTotal count of settled particles: {}\nSimulation time: {} s\nTime step: {} s\n",
                             particles_count, totalSettledCount, simtime, dt);

    bool ispopup{true};
    if (std::find(argv, argv + argc, std::string("-nopopup")) != argv + argc)
        ispopup = false;

    if (ispopup)
        gmsh::fltk::run();

    gmsh::finalize();

    return EXIT_SUCCESS;
}
