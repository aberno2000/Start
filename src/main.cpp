#include <aabb/AABB.h>
#include <algorithm>
#include <cstring>
#include <format>
#include <fstream>
#include <gmsh.h>
#include <hdf5.h>
#include <iostream>
#include <ranges>
#include <span>
#include <string_view>

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

ParticlesGeneric createParticles(size_t count)
{
    RealNumberGenerator rng;
    ParticlesGeneric particles(count);

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

ParticleVectorSimple truncateParticlesToXYZR(ParticlesGeneric particles)
{
    ParticleVectorSimple filtered;
    for (auto const &particle : particles)
        filtered.push_back({particle.getX(), particle.getY(), particle.getZ(), particle.getRadius()});
    return filtered;
}

void simulateMovement(ParticlesGeneric &pgs, aabb::AABB const &bounding_volume, double dt, double total_time)
{
    for (double t{}; t <= total_time; t += dt)
        pgs.erase(std::remove_if(pgs.begin(), pgs.end(), [dt, bounding_volume](auto &p)
                                 {
            p.updatePosition(dt);
            return p.isOutOfBounds(bounding_volume); }));
}

int main(int argc, char *argv[])
{
    gmsh::initialize();

    aabb::AABB bounding_box({0, 0, 0}, {100, 100, 100});
    ParticlesGeneric pgs(createParticles(1'000)); // 1'000'000 for Intel(R) Core(TM) i5-5300U CPU @ 2.30GHz
                                                  // is harmful if synchronize models in gmsh

    VolumeCreator::createBox();
    Mesh::setMeshSize(0.75);
    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(2);

    auto particles{truncateParticlesToXYZR(pgs)};
    VolumeCreator::createSpheres(std::span<ParticleSimple const>(particles.data(), particles.size()));
    gmsh::model::occ::synchronize();

    gmsh::write("results/mesh.msh");
    TriangleMeshParams meshParams{Mesh::getMeshParams("results/mesh.msh")};
    HDF5Handler hdf5handler("results/mesh.hdf5");
    hdf5handler.saveMeshToHDF5(meshParams);

    // settled = simulate_movement_of_particles(particles, triangles, 0.1, 0.3)
    // save_settled_to_hdf5(settled, "../results/settled.hdf5")
    // settled = read_settled_hdf5("../results/settled.hdf5")
    // for x in settled:
    //     print(" ".join(str(val) for val in x) + "\n")

    bool ispopup{true};
    for (int argid{1}; argid < argc; ++argid)
        if (strcmp(argv[argid], "-nopopup") == 0)
            ispopup = false;

    if (ispopup)
        gmsh::fltk::run();

    gmsh::finalize();

    // simulateMovement(pgs, bounding_box, 0.1, 1);

    return EXIT_SUCCESS;
}
