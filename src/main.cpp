#include <format>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"

void writeInXYZ(std::span<Particle const> particles, std::string_view filename)
{
    std::ofstream ofs(std::string(filename).c_str());
    if (!ofs.is_open())
    {
#ifdef LOG
        ERRMSG(std::format("Can't open file {}", filename));
#endif
        return;
    }

    ofs << particles.size() - 1 << '\n';
    for (auto const &particle : particles)
        ofs << std::format("0 {} {} {}\n",
                           particle.getX(), particle.getY(), particle.getZ());
    ofs.close();

#ifdef LOG
    LOGMSG(std::format("File {} filled successfully with {} particles", filename, particles.size()));
#endif
}

#define N 10'000

int main()
{
    RealNumberGenerator rng;
    std::vector<Particle> particles(N);

    for (size_t i{}; i < N; ++i)
        particles[i] = Particle(rng.get_double(0, 100),
                                rng.get_double(0, 100),
                                rng.get_double(0, 100),
                                rng.get_double(0, 5),
                                rng.get_double(0, 5),
                                rng.get_double(0, 5),
                                rng.get_double(0.5, 1));

#ifdef LOG
    LOGMSG(std::format("Filled {} particles", particles.size()));
#endif

    // O(n^2)
    for (size_t i{}; i < particles.size(); ++i)
    {
        const aabb::AABB &currentAABB{particles[i].getBoundingBox()};
        particles[i].updatePosition();

        for (auto j{i + 1}; j < particles.size(); ++j)
        {
            if (currentAABB.overlaps(particles[j].getBoundingBox(), true))
            {
                // If AABBs overlap, perform detailed collision check
                if (particles[i].overlaps(particles[j]))
                {
                    // TODO: if overlap -> update velocity
#ifdef LOG
                    LOGMSG(std::format("\033[1;33mOverlap detected: \033[1;34m{}<--->{}\033[0m\033[1m", i, j));
                    LOGMSG(std::format("\033[1;34m{} particle\033[0m\033[1m: x = {:.6f}\ty = {:.6f}\tz = {:.6f}\tradius = {:.6f}",
                                       i,
                                       particles[i].getX(),
                                       particles[i].getY(),
                                       particles[i].getZ(),
                                       particles[i].getRadius()));
                    LOGMSG(std::format("\033[1;34m{} particle\033[0m\033[1m: x = {:.6f}\ty = {:.6f}\tz = {:.6f}\tradius = {:.6f}",
                                       j,
                                       particles[j].getX(),
                                       particles[j].getY(),
                                       particles[j].getZ(),
                                       particles[j].getRadius()));
#endif
                }
            }
        }
    }

    writeInXYZ(std::span<Particle const>(particles.data(), particles.size()), "trajectory.xyz");

    return EXIT_SUCCESS;
}
