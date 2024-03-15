#ifndef PARTICLES_HPP
#define PARTICLES_HPP

#include <CGAL/Bbox_3.h>
#include <atomic>

#include "../Geometry/MathVector.hpp"
#include "../Utilities/Constants.hpp"
#include "../Utilities/Utilities.hpp"

using namespace constants;
using namespace particle_types;
using namespace physical_constants;
using namespace viscosity_temperature_index;
using namespace VSS_deflection_parameter;

/// @brief Represents a particle in a simulation.
class Particle
{
private:
    static std::atomic<size_t> m_nextId; ///< Static member for generating unique IDs.
    size_t m_id;                         ///< Id of the particle.
    ParticleType m_type{};               ///< Type of the particle.
    Point3 m_centre;                     ///< Position in Cartesian coordinates (x, y, z).
    VelocityVector m_velocity;           ///< Velocity vector (Vx, Vy, Vz).
    double m_energy{};                   ///< Particle energy [J].
    CGAL::Bbox_3 m_bbox;                 ///< Bounding box for particle.

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
        case ParticleType::Ne:
            return Ne_radius;
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
        case ParticleType::Ne:
            return Ne_mass;
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
     * @brief Gets viscosity temperature index from the specified type of the particle.
     * @param type Type of the particle represented as enum.
     * @return viscosity temperature index of the particle [no measure units].
     */
    constexpr double getViscosityTemperatureIndexFromType(ParticleType type) const
    {
        switch (type)
        {
        case ParticleType::Ar:
            return Ar_VTI;
        case ParticleType::Ne:
            return Ne_VTI;
        case ParticleType::He:
            return He_VTI;
        default:
            return 0;
        }
    }

    /**
     * @brief Gets VSS deflection parameter from the specified type of the particle.
     * @param type Type of the particle represented as enum.
     * @return VSS deflection parameter of the particle [no measure units].
     */
    constexpr double getVSSDeflectionParameterFromType(ParticleType type) const
    {
        switch (type)
        {
        case ParticleType::Ar:
            return Ar_VSS_TI;
        case ParticleType::Ne:
            return Ne_VSS_TI;
        case ParticleType::He:
            return He_VSS_TI;
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
    void calculateEnergyJFromVelocity(VelocityVector &&v) noexcept;

    /// @brief Calculates bounding box for the current particle.
    void calculateBoundingBox();

public:
    Particle() : m_bbox(0, 0, 0, 0, 0, 0) {}
    Particle(ParticleType type_);
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

    /* === Getters for particle params. === */
    constexpr size_t getId() const { return m_id; }
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
    constexpr CGAL::Bbox_3 const &getBoundingBox() const { return m_bbox; }
    constexpr double getMass() const { return getMassFromType(m_type); }
    constexpr double getRadius() const { return getRadiusFromType(m_type); }
    constexpr float getViscosityTemperatureIndex() const { return getViscosityTemperatureIndexFromType(m_type); }
    constexpr float getVSSDeflectionParameter() const { return getVSSDeflectionParameterFromType(m_type); }

    /**
     * @brief Chooses the specified scattering model.
     * @param target particle of gas with which current particle will colide.
     * @param n_concentration concentration of particles.
     * @param model scattering model (available: HS/VHS/VSS)
     * @param time_step simulation time step.
     * @return `true` if colided, otherwise `false`.
     */
    bool colide(Particle target, double n_concentration, std::string_view model, double time_step);

    bool colideHS(Particle target, double n_concentration, double time_step);
    bool colideVHS(Particle target, double n_concentration, double omega, double time_step);
    bool colideVSS(Particle target, double n_concentration, double omega, double alpha, double time_step);
};

using ParticleVector = std::vector<Particle>;

/// @brief Generates a vector of particles with specified velocity ranges.
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double x, double y, double z,
                                             double vx, double vy, double vz);
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double x, double y, double z,
                                             double minvx = 50.0, double minvy = 50.0, double minvz = 50.0,
                                             double maxvx = 100.0, double maxvy = 100.0, double maxvz = 100.0);
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                             double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                             double minvx = 10.0, double minvy = 10.0, double minvz = 10.0,
                                             double maxvx = 20.0, double maxvy = 20.0, double maxvz = 20.0);

/// @brief Creates a vector of particles with specified properties.
ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
                                         double x, double y, double z,
                                         double minenergy = 30.0, double maxenergy = 50.0);
ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
                                         double minx = 0.0, double miny = 0.0, double minz = 0.0,
                                         double maxx = 100.0, double maxy = 100.0, double maxz = 100.0,
                                         double minenergy = 30.0, double maxenergy = 50.0);

#endif // !PARTICLES_HPP
