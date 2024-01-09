#include <format>
#include <fstream>
#include <iostream>
#include <span>
#include <string_view>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"

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
        particles[i] = ParticleGeneric(rng.get_double(0, 100),
                                       rng.get_double(0, 100),
                                       rng.get_double(0, 100),
                                       rng.get_double(0, 5),
                                       rng.get_double(0, 5),
                                       rng.get_double(0, 5),
                                       rng.get_double(1, 2.5));
    return particles;
}

int main()
{
    ParticlesGeneric pg(createParticles(50));
    writeInFile(std::span<ParticleGeneric const>(pg.data(), pg.size()), "results/particles.txt");

    return EXIT_SUCCESS;
}
