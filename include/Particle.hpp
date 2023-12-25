#ifndef PARTICLE_HPP
#define PARTICLE_HPP

#include <aabb/AABB.h>
#include <vector>

#include "MathVector.hpp"

/// @brief Represents a particle in a simulation.
class Particle
{
private:
    PositionVector m_cords;                                    // Position in Cartesian coordinates (x, y, z).
    VelocityVector m_velocity;                                 // Velocity vector (Vx, Vy, Vz).
    double m_radius{},                                         // Particle radius.
        m_minBoundary{}, m_maxBoundary{kdefault_max_boundary}; // Min and max boundaries.
    aabb::AABB m_boundingBox;                                  // Axis-aligned bounding box

    static constexpr double kdefault_min_boundary{},
        kdefault_max_boundary{100.0};

public:
    Particle() {}
    Particle(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_,
             double minBoundary_ = kdefault_min_boundary, double maxBoundary_ = kdefault_max_boundary);
    Particle(PositionVector posvec, double vx_, double vy_, double vz_, double radius_,
             double minBoundary_ = kdefault_min_boundary, double maxBoundary_ = kdefault_max_boundary);
    Particle(double x_, double y_, double z_, VelocityVector velvec, double radius_,
             double minBoundary_ = kdefault_min_boundary, double maxBoundary_ = kdefault_max_boundary);
    Particle(PositionVector posvec, VelocityVector velvec,
             double radius_, double minBoundary_ = kdefault_min_boundary, double maxBoundary_ = kdefault_max_boundary);
    ~Particle() {}

    /**
     * @brief Updates the position of the particle after a time interval.
     * @param dt Time interval for the update (default = 1).
     */
    void updatePosition(double dt = 1);

    /**
     * @brief Checks if the current particle overlaps with another particle.
     * @param other The other Particle to check against.
     * @return `true` if the particles overlap, otherwise `false`.
     */
    bool overlaps(Particle const &other) const;

    /**
     * @brief Checks if the particle out of specified bounds.
     * @return `true` if the particle out of bounds, otherwise `false`.
     */
    bool isOutOfBounds() const;

    /* === Getters for particle params. === */
    constexpr double getX() const { return m_cords.getX(); }
    constexpr double getY() const { return m_cords.getY(); }
    constexpr double getZ() const { return m_cords.getZ(); }
    constexpr double getPositionModule() const { return m_cords.module(); }
    constexpr double getVx() const { return m_velocity.getX(); }
    constexpr double getVy() const { return m_velocity.getY(); }
    constexpr double getVz() const { return m_velocity.getZ(); }
    constexpr double getVelocityModule() const { return m_velocity.module(); }
    constexpr double getRadius() const { return m_radius; }
    constexpr double getMinBoundary() const { return m_minBoundary; }
    constexpr double getMaxBoundary() const { return m_maxBoundary; }
    constexpr PositionVector const &getPositionVector() const { return m_cords; }
    constexpr VelocityVector const &getVelocityVector() const { return m_velocity; }
    constexpr aabb::AABB const &getBoundingBox() const { return m_boundingBox; }

    void Colide(double xi, double phi, double p_mass, double t_mass);

    /* === Virtual getters for specific particles like Argon, Beryllium, etc. === */
    // virtual constexpr double getWeigth() const = 0;
    // virtual constexpr double getScattering() const = 0;
};

// TODO: 1. Make `Particle` abstract; 2. Add more specific classes

/* class ParticleArgon : public Particle
{
public:
    constexpr double getWeigth() const override { return 6.6335209e-26; }
    constexpr double getScattering() const override { return ...; }
};

class ParticleBeryllium : public Particle
{
public:
    constexpr double getWeigth() const override { return 1.4965076e-26; }
    constexpr double getScattering() const override { return ...; }
}; */

/* --> Alias for many of particles. <-- */
using Particles = std::vector<Particle>;

#endif // !PARTICLE_HPP
