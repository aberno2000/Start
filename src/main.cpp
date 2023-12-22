#include <fstream>
#include <iomanip>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"

#define N 10'000

void writeInFile(Particle particle, std::string_view filename)
{
    std::ofstream ofs(std::string(filename).c_str(), std::ios_base::app);
    if (!ofs.is_open())
    {
#ifdef LOG
        ERRMSG(std::format("Can't open file {}", filename));
#endif
        return;
    }

    ofs << std::format("{} {} {}\n",
                       particle.getX(), particle.getY(), particle.getZ());
    ofs.close();

#ifdef LOG
    LOGMSG(std::format("File {} filled successfully", filename));
#endif
}

void writeInFile(std::span<Particle const> particles, std::string_view filename)
{
    std::ofstream ofs(std::string(filename).c_str());
    if (!ofs.is_open())
    {
#ifdef LOG
        ERRMSG(std::format("Can't open file {}", filename));
#endif
        return;
    }

    for (auto const &particle : particles)
        ofs << std::format("{} {} {} {} {} {} {}\n",
                           particle.getX(), particle.getY(), particle.getZ(),
                           particle.getVx(), particle.getVy(), particle.getVz(),
                           particle.getRadius());
    ofs.close();

#ifdef LOG
    LOGMSG(std::format("File {} filled successfully with {} particles", filename, particles.size()));
#endif
}

int main()
{
    RealNumberGenerator rng;
    Particles v(N);

    for (size_t i{}; i < N; ++i)
    {
        v[i] = Particle(rng.get_double(0, 100),
                        rng.get_double(0, 100),
                        rng.get_double(0, 100),
                        rng.get_double(0, 5),
                        rng.get_double(0, 5),
                        rng.get_double(0, 5),
                        rng.get_double(0.5, 1));
    }

    double time{}, time_step{0.01};
    while (time < 10)
    {
        for (auto it{v.begin()}, end{v.end()}; it != end; ++it)
        {
            it->updatePosition(time_step);
            if (it->isOutOfBounds())
            {
                writeInFile(*it, "OutOfBounds.txt");
                v.erase(it);
            }
            time += time_step;
        }
    }

    std::cout << std::format("Remains {} particles\n", v.size());

    /* std::vector<Particle> particles(N);
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

    // Simulating movement
    double time{}, time_step{0.1};
    while (time < 10)
    {
        // O(n^2)
        for (size_t i{}; i < particles.size(); ++i)
        {
            const aabb::AABB &currentAABB{particles[i].getBoundingBox()};
            particles[i].updatePosition(time_step);
            time += time_step;

            for (auto j{i + 1}; j < particles.size(); ++j)
            {
                // If AABBs overlap, perform detailed collision check
                if (currentAABB.overlaps(particles[j].getBoundingBox(), true))
                {
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
    }

    writeInFile(std::span<Particle const>(particles.data(), particles.size()), "particles.txt"); */
    return EXIT_SUCCESS;
}
