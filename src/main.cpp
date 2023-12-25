#include <fstream>
#include <iomanip>
#include <numbers>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"

#define N 10'000

void writeInFile(ParticleGeneric particle, std::string_view filename)
{
    std::ofstream ofs(std::string(filename).c_str(), std::ios_base::app);
    if (!ofs.is_open())
    {
#ifdef LOG
        ERRMSG(std::format("Can't open file {}", filename));
#endif
        return;
    }

    ofs << std::format("{} {} {} {}\n",
                       particle.getX(), particle.getY(), particle.getZ(), particle.getRadius());
    ofs.close();

#ifdef LOG_SINGLE_WRITE
    LOGMSG(std::format("File {} filled successfully", filename));
#endif
}

void writeInFile(std::span<ParticleGeneric const> particles, std::string_view filename)
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

void simulateOutOfBounds()
{
    RealNumberGenerator rng;
    ParticlesGeneric particles(createParticles(N));

    double time{}, time_step{0.01};

    {
        std::ofstream ofs(std::string("OutOfBounds.txt").c_str(), std::ios_base::app);
        if (!ofs.is_open())
            return;
        ofs << settings::getCurTime("%D %H:%M:%S") << '\n';
        ofs.close();
    }

    while (time < 10)
    {
        for (auto it{particles.begin()}, end{particles.end()}; it != end; ++it)
        {
            it->updatePosition(time_step);
            if (it->isOutOfBounds())
            {
                writeInFile(*it, "OutOfBounds.txt");
                particles.erase(it);
            }
            time += time_step;
        }
    }

    std::cout << std::format("Remains {} particles\n", particles.size());
}

void simulateCollision()
{
    RealNumberGenerator rng;
    ParticlesGeneric particles(createParticles(N));

    double time{}, time_step{0.01};
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
                        // TODO: if overlap -> update velocity)
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

    writeInFile(std::span<ParticleGeneric const>(particles.data(), particles.size()), "particles.txt");
}

void showSizes()
{
    std::cout << std::format(R"(sizeof(ParticleGeneric) = {} bytes
sizeof(MathVector) = {}x2
sizeof(AABB) = {}
sizeof(double) = {}x3
sizeof(ParticleArgon) = {}
sizeof(ParticleAluminium) = {}
)",
                             sizeof(ParticleGeneric), sizeof(MathVector), sizeof(aabb::AABB),
                             sizeof(double), sizeof(ParticleArgon), sizeof(ParticleAluminium));
}

int main()
{
    return EXIT_SUCCESS;
}
