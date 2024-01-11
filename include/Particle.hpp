#ifndef PARTICLE_HPP
#define PARTICLE_HPP

#include <aabb/AABB.h>
#include <concepts>
#include <limits>
#include <tuple>
#include <vector>

#include "MathVector.hpp"
#include "Mesh.hpp"
#include "Settings.hpp"

/// @brief Represents a particle in a simulation.
class ParticleGeneric
{
private:
    PositionVector m_cords;    // Position in Cartesian coordinates (x, y, z).
    VelocityVector m_velocity; // Velocity vector (Vx, Vy, Vz).
    double m_radius{},         // Particle radius.
        m_energy{};            // Particle energy [J].
    aabb::AABB m_boundingBox;  // Axis-aligned bounding box

    /**
     * @brief Calculates velocity module from energy of particle and then
     * calculates Vx, Vy, Vz from this module using random numbers.
     * Formula:
     * |V| = √(2⋅E/mass)
     * @param energy Energy of the particle in [J].
     * @return Velocity module.
     */
    void calculateVelocityFromEnergy_J();

public:
    ParticleGeneric() {}
    ParticleGeneric(double x_, double y_, double z_, double energy_, double radius_);
    ParticleGeneric(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_);
    ParticleGeneric(PositionVector posvec, double vx_, double vy_, double vz_, double radius_);
    ParticleGeneric(PositionVector posvec, double energy_, double radius_);
    ParticleGeneric(double x_, double y_, double z_, VelocityVector velvec, double radius_);
    ParticleGeneric(PositionVector posvec, VelocityVector velvec, double radius_);
    virtual ~ParticleGeneric() {}

    /**
     * @brief Updates the position of the particle after a time interval.
     * @param dt Time interval for the update (default = 1) [s].
     */
    void updatePosition(double dt = 1);

    /**
     * @brief Checks if the current particle overlaps with another particle.
     * @param other The other Particle to check against.
     * @return `true` if the particles overlap, otherwise `false`.
     */
    bool overlaps(ParticleGeneric const &other) const;

    /**
     * @brief Checks if the particle out of specified bounds.
     * @param bounding_volume Bounding volume.
     * @return `true` if the particle out of bounds, otherwise `false`.
     */
    bool isOutOfBounds(aabb::AABB const &bounding_volume) const;

    /**
     * @brief Checks if the particle is inside a specified triangle.
     * @details This function determines whether the particle is inside the triangle
     *          defined by the vertices in 'triangleVertices'. It uses a geometric
     *          algorithm suitable for 3D space to check if the particle lies
     *          within the boundaries of the triangle.
     * @param mesh A tuple representing the vertices of the triangle.
     *        Each vertex is a 'PositionVector' defining a point in 3D space.
     * @return The ID of the triangle where the particle has settled, as indicated
     *         by the first element of 'mesh', if the particle is inside the triangle.
     *         Returns `-1` if the particle is not inside the triangle or if it does not
     *         lie in the same plane as the triangle.
     */
    int isParticleInsideTriangle(TriangleMeshParam const &mesh) const;

    /* === Getters for particle params. === */
    constexpr double getX() const { return m_cords.getX(); }
    constexpr double getY() const { return m_cords.getY(); }
    constexpr double getZ() const { return m_cords.getZ(); }
    constexpr double getPositionModule() const { return m_cords.module(); }
    constexpr double getEnergy_J() const { return m_energy; }
    double getEnergy_eV() const { return m_energy * settings::physical_constants::J_eV; }
    constexpr double getVx() const { return m_velocity.getX(); }
    constexpr double getVy() const { return m_velocity.getY(); }
    constexpr double getVz() const { return m_velocity.getZ(); }
    constexpr double getVelocityModule() const { return m_velocity.module(); }
    constexpr double getRadius() const { return m_radius; }
    constexpr PositionVector const &getPositionVector() const { return m_cords; }
    constexpr VelocityVector const &getVelocityVector() const { return m_velocity; }
    constexpr aabb::AABB const &getBoundingBox() const { return m_boundingBox; }

    /**
     * @brief Calculates the collision of a particle with another particle or object.
     * @param xi The angle of incidence in radians.
     * @param phi The azimuthal angle in radians.
     * @param p_mass The mass of the particle.
     * @param t_mass The mass of the target object.
     */
    void colide(double xi, double phi, double p_mass, double t_mass);

    /* === Virtual getters for specific particles like Argon, Beryllium, etc. === */
    /// @return Minimal value of `double` type as a default value.
    virtual constexpr double getMass() const { return std::numeric_limits<double>::min(); };
    // virtual constexpr double getScattering() const { return 0; };
};

class ParticleArgon final : public ParticleGeneric
{
private:
    static constexpr double radius{98e-12};

public:
    ParticleArgon() : ParticleGeneric() {}
    ParticleArgon(double x_, double y_, double z_, double energy_, double radius_)
        : ParticleGeneric(x_, y_, z_, energy_, radius_ = radius) {}
    ParticleArgon(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_ = radius)
        : ParticleGeneric(x_, y_, z_, vx_, vy_, vz_, radius_) {}
    ParticleArgon(PositionVector posvec, double vx_, double vy_, double vz_, double radius_ = radius)
        : ParticleGeneric(posvec, vx_, vy_, vz_, radius_) {}
    ParticleArgon(PositionVector posvec, double energy_, double radius_)
        : ParticleGeneric(posvec, energy_, radius_ = radius) {}
    ParticleArgon(double x_, double y_, double z_, VelocityVector velvec, double radius_ = radius)
        : ParticleGeneric(x_, y_, z_, velvec, radius_) {}
    ParticleArgon(PositionVector posvec, VelocityVector velvec,
                  double radius_ = radius)
        : ParticleGeneric(posvec, velvec, radius_) {}

    constexpr double getMass() const override { return 6.6335209e-26; }
    // constexpr double getScattering() const override { return ...; }
};

class ParticleAluminium final : public ParticleGeneric
{
private:
    static constexpr double radius{143e-12};

public:
    ParticleAluminium() : ParticleGeneric() {}
    ParticleAluminium(double x_, double y_, double z_, double energy_, double radius_)
        : ParticleGeneric(x_, y_, z_, energy_, radius_ = radius) {}
    ParticleAluminium(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_ = radius)
        : ParticleGeneric(x_, y_, z_, vx_, vy_, vz_, radius_) {}
    ParticleAluminium(PositionVector posvec, double vx_, double vy_, double vz_, double radius_ = radius)
        : ParticleGeneric(posvec, vx_, vy_, vz_, radius_) {}
    ParticleAluminium(PositionVector posvec, double energy_, double radius_)
        : ParticleGeneric(posvec, energy_, radius_ = radius) {}
    ParticleAluminium(double x_, double y_, double z_, VelocityVector velvec, double radius_ = radius)
        : ParticleGeneric(x_, y_, z_, velvec, radius_) {}
    ParticleAluminium(PositionVector posvec, VelocityVector velvec, double radius_ = radius)
        : ParticleGeneric(posvec, velvec, radius_) {}

    constexpr double getMass() const override { return 4.4803831e-26; }
    // constexpr double getScattering() const override { return ...; }
};

/// @brief x, y, z, Vx, Vy, Vz, radius
using ParticleVectorWithVelocities = std::vector<std::tuple<PositionVector,
                                                            double, double, double,
                                                            double>>;
/// @brief x, y, z, E, radius
using ParticleVectorWithEnergy = std::vector<std::tuple<PositionVector,
                                                        double, double>>;
/// @brief x, y, z, radius
using ParticleVectorSimple = std::vector<std::tuple<PositionVector, double>>;
using ParticleSimple = std::tuple<PositionVector, double>;

/* --> Aliases for many of specific kind particles. <-- */
using ParticleGenericVector = std::vector<ParticleGeneric>;
using ParticleArgonVector = std::vector<ParticleArgon>;
using ParticleAluminiumVector = std::vector<ParticleAluminium>;

#endif // !PARTICLE_HPP
