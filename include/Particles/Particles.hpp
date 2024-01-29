#ifndef PARTICLES_HPP
#define PARTICLES_HPP

#include <aabb/AABB.h>

#include "../Geometry/MathVector.hpp"
#include "../Utilities/Constants.hpp"
#include "../Utilities/Settings.hpp"

using namespace constants;
using namespace particle_types;
using namespace physical_constants;

/// @brief Represents a particle in a simulation.
class Particle
{
private:
    ParticleType m_type{};     // Type of the particle.
    Point3 m_centre;           // Position in Cartesian coordinates (x, y, z).
    VelocityVector m_velocity; // Velocity vector (Vx, Vy, Vz).
    double m_energy{};         // Particle energy [J].
    aabb::AABB m_boundingBox;  // Axis-aligned bounding box.

    /**
     * @brief Gets radius from the specified type of the particle.
     * @param type Type of the particle represented as enum.
     * @return Radius of the particle [m].
     */
    constexpr double getRadiusFromType(ParticleType type) const
    {
        switch (type)
        {
        case ParticleType::Ar:
            return Ar_radius;
        case ParticleType::N:
            return N_radius;
        case ParticleType::He:
            return He_radius;
        case ParticleType::Ti:
            return Ti_radius;
        case ParticleType::Al:
            return Al_radius;
        case ParticleType::Sn:
            return Sn_radius;
        case ParticleType::W:
            return W_radius;
        case ParticleType::Au:
            return Au_radius;
        case ParticleType::Cu:
            return Cu_radius;
        case ParticleType::Ni:
            return Ni_radius;
        case ParticleType::Ag:
            return Ag_radius;
        default:
            return 0;
        }
    }

    /**
     * @brief Gets mass from the specified type of the particle.
     * @param type Type of the particle represented as enum.
     * @return Mass of the particle [kg].
     */
    constexpr double getMassFromType(ParticleType type) const
    {
        switch (type)
        {
        case ParticleType::Ar:
            return Ar_mass;
        case ParticleType::N:
            return N_mass;
        case ParticleType::He:
            return He_mass;
        case ParticleType::Ti:
            return Ti_mass;
        case ParticleType::Al:
            return Al_mass;
        case ParticleType::Sn:
            return Sn_mass;
        case ParticleType::W:
            return W_mass;
        case ParticleType::Au:
            return Au_mass;
        case ParticleType::Cu:
            return Cu_mass;
        case ParticleType::Ni:
            return Ni_mass;
        case ParticleType::Ag:
            return Ag_mass;
        default:
            return 0;
        }
    }

    /**
     * @brief Calculates velocity module from energy of particle and then
     * calculates Vx, Vy, Vz from this module using random numbers.
     * Formula:
     * |V| = √(2⋅E/mass)
     * @param energy Energy of the particle in [J].
     * @return Velocity module.
     */
    void calculateVelocityFromEnergy_J();

    /**
     * @brief Calculates the kinetic energy of a particle from its velocity components.
     *
     * This function uses the formula for kinetic energy:
     * E = 0.5 * mass * |V|^2,
     * where |V| is the magnitude of the velocity vector. The function assumes
     * that the mass of the particle is known and accessible within the class.
     *
     * @param vx The x-component of the velocity in [m/s].
     * @param vy The y-component of the velocity in [m/s].
     * @param vz The z-component of the velocity in [m/s].
     * @return void The function does not return a value but presumably updates
     * the energy state of the particle within the class.
     */
    void calculateEnergyJFromVelocity(double vx, double vy, double vz);
    void calculateEnergyJFromVelocity(VelocityVector const &v);
    void calculateEnergyJFromVelocity(VelocityVector &&v) _GLIBCXX_NOEXCEPT;

public:
    Particle() {}
    Particle(ParticleType type_, double x_, double y_, double z_, double energy_);
    Particle(ParticleType type_, double x_, double y_, double z_, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point3 const &centre, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point3 &&centre, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point3 const &centre, double energy_);
    Particle(ParticleType type_, Point3 &&centre, double energy_);
    Particle(ParticleType type_, double x_, double y_, double z_, VelocityVector const &velvec);
    Particle(ParticleType type_, double x_, double y_, double z_, VelocityVector &&velvec);
    Particle(ParticleType type_, Point3 const &centre, VelocityVector const &velvec);
    Particle(ParticleType type_, Point3 &&centre, VelocityVector &&velvec);
    ~Particle() {}

    /**
     * @brief Updates the position of the particle after a time interval.
     * @param dt Time interval for the update [s].
     */
    void updatePosition(double dt);

    /**
     * @brief Checks if the current particle overlaps with another particle.
     * @param other The other Particle to check against.
     * @return `true` if the particles overlap, otherwise `false`.
     */
    bool overlaps(Particle const &other) const;
    bool overlaps(Particle &&other) const;

    /**
     * @brief Checks if the particle out of specified bounds.
     * @param bounding_volume Bounding volume.
     * @return `true` if the particle out of bounds, otherwise `false`.
     */
    bool isOutOfBounds(aabb::AABB const &bounding_volume) const;
    bool isOutOfBounds(aabb::AABB &&bounding_volume) const;

    /* === Getters for particle params. === */
    double getX() const;
    double getY() const;
    double getZ() const;
    double getPositionModule() const;
    constexpr double getEnergy_J() const { return m_energy; }
    double getEnergy_eV() const;
    constexpr double getVx() const { return m_velocity.getX(); }
    constexpr double getVy() const { return m_velocity.getY(); }
    constexpr double getVz() const { return m_velocity.getZ(); }
    double getVelocityModule() const;
    constexpr Point3 const &getCentre() const { return m_centre; }
    constexpr VelocityVector const &getVelocityVector() const { return m_velocity; }
    constexpr aabb::AABB const &getBoundingBox() const { return m_boundingBox; }
    constexpr double getMass() const { return getMassFromType(m_type); }
    constexpr double getRadius() const { return getRadiusFromType(m_type); }

    /**
     * @brief Calculates the collision of a particle with another particle or object.
     * @param p_mass The mass of the particle.
     * @param t_mass The mass of the target object.
     */
    void colide(double p_mass, double t_mass) &;
};

using ParticleVector = std::vector<Particle>;

/// @brief Generates a vector of particles with specified velocity ranges.
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                             double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                             double minvx = 10.0, double minvy = 10.0, double minvz = 10.0,
                                             double maxvx = 20.0, double maxvy = 20.0, double maxvz = 20.0)
{
    RealNumberGenerator rng;
    ParticleVector particles;

    for (size_t i{}; i < count; ++i)
    {
        double x{rng(minx, maxx)},
            y{rng(miny, maxy)},
            z{rng(minz, maxz)},
            vx{rng(minvx, maxvx)},
            vy{rng(minvy, maxvy)},
            vz{rng(minvz, maxvz)};

        particles.emplace_back(type, x, y, z, vx, vy, vz);
    }

    return particles;
}

/// @brief Creates a vector of particles with specified properties.
ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
                                         double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                         double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                         double minenergy = 30.0, double maxenergy = 50.0,
                                         double minradius = 1.0, double maxradius = 5.0)
{
    RealNumberGenerator rng;
    ParticleVector particles;

    for (size_t i{}; i < count; ++i)
    {
        double x{rng(minx, maxx)},
            y{rng(miny, maxy)},
            z{rng(minz, maxz)},
            energy{rng(minenergy, maxenergy)};

        particles.emplace_back(type, x, y, z, energy);
    }

    return particles;
}

#endif // !PARTICLES_HPP
