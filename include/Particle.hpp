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

/**
 * @brief Generates a vector of particles with specified velocity ranges.
 * 
 * @tparam T The type of particle to generate. It can be a specific particle type (e.g., ParticleArgon)
 *           or a generic particle type.
 * @param count The number of particles to generate.
 * @param minx Minimum x-coordinate for the particle's initial position.
 * @param miny Minimum y-coordinate for the particle's initial position.
 * @param minz Minimum z-coordinate for the particle's initial position.
 * @param maxx Maximum x-coordinate for the particle's initial position.
 * @param maxy Maximum y-coordinate for the particle's initial position.
 * @param maxz Maximum z-coordinate for the particle's initial position.
 * @param minvx Minimum x-component of the particle's velocity.
 * @param minvy Minimum y-component of the particle's velocity.
 * @param minvz Minimum z-component of the particle's velocity.
 * @param maxvx Maximum x-component of the particle's velocity.
 * @param maxvy Maximum y-component of the particle's velocity.
 * @param maxvz Maximum z-component of the particle's velocity.
 * @param minradius Minimum radius for generic particles (ignored for specific particle types).
 * @param maxradius Maximum radius for generic particles (ignored for specific particle types).
 * @return std::vector<T> A vector of generated particles.
 */
template <typename T>
std::vector<T> createParticlesWithVelocities(size_t count, double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                             double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                             double minvx = 10.0, double minvy = 10.0, double minvz = 10.0,
                                             double maxvx = 20.0, double maxvy = 20.0, double maxvz = 20.0,
                                             double minradius = 1.0, double maxradius = 5.0);

/**
 * @brief Creates a vector of particles with specified properties.
 * @details This template function generates a list of particles of type T. 
 *          The particles are initialized with random positions (x, y, z), energy, and radius.
 *          For ParticleArgon and ParticleAluminium, a predefined radius is used.
 * @tparam T The particle type (e.g., ParticleArgon, ParticleAluminium).
 * @param count The number of particles to generate.
 * @param minx The minimum x-coordinate for particle position (default: 0.0).
 * @param miny The minimum y-coordinate for particle position (default: 0.0).
 * @param minz The minimum z-coordinate for particle position (default: 0.0).
 * @param maxx The maximum x-coordinate for particle position (default: 100.0).
 * @param maxy The maximum y-coordinate for particle position (default: 100.0).
 * @param maxz The maximum z-coordinate for particle position (default: 100.0).
 * @param minenergy The minimum energy value for a particle (default: 30.0).
 * @param maxenergy The maximum energy value for a particle (default: 50.0).
 * @param minradius The minimum radius for a particle (default: 1.0).
 * @param maxradius The maximum radius for a particle (default: 5.0).
 * @return std::vector<T> A vector containing the generated particles.
 */
template <typename T>
std::vector<T> createParticlesWithEnergy(size_t count, double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                         double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                         double minenergy = 30.0, double maxenergy = 50.0,
                                         double minradius = 1.0, double maxradius = 5.0);

#include "ParticleImpl.hpp"

#endif // !PARTICLE_HPP
