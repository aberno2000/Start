#ifndef PARTICLESIMPL_HPP
#define PARTICLESIMPL_HPP

#include "../Generators/RealNumberGenerator.hpp"

template <typename T>
std::vector<T> createParticlesWithVelocities(size_t count, double minx, double miny, double minz,
                                             double maxx, double maxy, double maxz,
                                             double minvx, double minvy, double minvz,
                                             double maxvx, double maxvy, double maxvz,
                                             double minradius, double maxradius)
{
    RealNumberGenerator rng;
    std::vector<T> particles;

    for (size_t i{}; i < count; ++i)
    {
        double x{rng.get_double(minx, maxx)},
            y{rng.get_double(miny, maxy)},
            z{rng.get_double(minz, maxz)},
            vx{rng.get_double(minvx, maxvx)},
            vy{rng.get_double(minvy, maxvy)},
            vz{rng.get_double(minvz, maxvz)};

        if constexpr (std::is_same_v<T, ParticleArgon> || std::is_same_v<T, ParticleAluminium>)
            particles.emplace_back(x, y, z, vx, vy, vz, T().getRadius());
        else
        {
            double radius{rng(minradius, maxradius)};
            particles.emplace_back(x, y, z, vx, vy, vz, radius);
        }
    }

    return particles;
}

template <typename T>
std::vector<T> createParticlesWithEnergy(size_t count, double minx, double miny, double minz,
                                         double maxx, double maxy, double maxz,
                                         double minenergy, double maxenergy,
                                         double minradius, double maxradius)
{
    RealNumberGenerator rng;
    std::vector<T> particles;

    for (size_t i{}; i < count; ++i)
    {
        double x{rng.get_double(minx, maxx)},
            y{rng.get_double(miny, maxy)},
            z{rng.get_double(minz, maxz)},
            energy{rng.get_double(minenergy, maxenergy)};

        if constexpr (std::is_same_v<T, ParticleArgon> || std::is_same_v<T, ParticleAluminium>)
            particles.emplace_back(x, y, z, energy, T().getRadius());
        else
        {
            double radius{rng.get_double(minradius, maxradius)};
            particles.emplace_back(x, y, z, energy, radius);
        }
    }

    return particles;
}

#endif // !PARTICLESIMPL_HPP
