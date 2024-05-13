#ifndef PARTICLES_HPP
#define PARTICLES_HPP

#include <CGAL/Bbox_3.h>
#include <atomic>

#include "../Geometry/CGALTypes.hpp"
#include "../Geometry/MathVector.hpp"
#include "../Utilities/Constants.hpp"

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
    Point m_centre;                      ///< Position in Cartesian coordinates (x, y, z).
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
            WARNINGMSG("Viscosity temperature index is 0 - it means smth went wrong while simulation with VHS or VSS, or you passed wrong particle type");
            return 0.0;
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
            WARNINGMSG("VSS deflection parameter is 0 - it means smth went wrong while simulation with VHS or VSS, or you passed wrong particle type");
            return 0.0;
        }
    }

    /**
     * @brief Gets charge from the specified type of the particle.
     * @param type Type of the particle represented as enum.
     * @return Charge of the particle [C - columbs].
     */
    constexpr double getChargeFromType(ParticleType type) const
    {
        switch (type)
        {
        case ParticleType::Ti:
            return ion_charges_coulombs::Ti_2plus; // By default returning 2 ion Ti.
        case ParticleType::Al:
            return ion_charges_coulombs::Al_3plus;
        case ParticleType::Sn:
            return ion_charges_coulombs::Sn_2plus; // By default returning 2 ion Sn.
        case ParticleType::W:
            return ion_charges_coulombs::W_6plus;
        case ParticleType::Au:
            return ion_charges_coulombs::Au_3plus; // By default returning 3 ion Au.
        case ParticleType::Cu:
            return ion_charges_coulombs::Cu_1plus; // By defaule returning 1 ion Cu.
        case ParticleType::Ni:
            return ion_charges_coulombs::Ni_2plus;
        case ParticleType::Ag:
            return ion_charges_coulombs::Ag_1plus;
        default:
            WARNINGMSG("Charge of the atom is 0 - it means smth went wrong or you passed unknown particle type, or it's a noble gas");
            return 0.0;
        }
    }

    /**
     * @brief Calculates velocity module from energy of particle and then
     * calculates Vx, Vy, Vz from this module using random numbers.
     * Formula:
     * |V| = √(2⋅E/mass)
     * @param thetaPhi Polar angle θ and azimuthal angle φ.
     * @return Velocity module.
     */
    void calculateVelocityFromEnergy_J(std::array<double, 3> const &thetaPhi);

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
    Particle(ParticleType type_, double x_, double y_, double z_, double energyJ_, std::array<double, 3> const &thetaPhi);
    Particle(ParticleType type_, double x_, double y_, double z_, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point const &centre, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point &&centre, double vx_, double vy_, double vz_);
    Particle(ParticleType type_, Point const &centre, double energyJ_, std::array<double, 3> const &thetaPhi);
    Particle(ParticleType type_, Point &&centre, double energyJ_, std::array<double, 3> const &thetaPhi);
    Particle(ParticleType type_, double x_, double y_, double z_, VelocityVector const &velvec);
    Particle(ParticleType type_, double x_, double y_, double z_, VelocityVector &&velvec);
    Particle(ParticleType type_, Point const &centre, VelocityVector const &velvec);
    Particle(ParticleType type_, Point &&centre, VelocityVector &&velvec);
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
    constexpr Point const &getCentre() const { return m_centre; }
    constexpr VelocityVector const &getVelocityVector() const { return m_velocity; }
    constexpr CGAL::Bbox_3 const &getBoundingBox() const { return m_bbox; }
    constexpr ParticleType getType() const { return m_type; }
    constexpr double getMass() const { return getMassFromType(m_type); }
    constexpr double getRadius() const { return getRadiusFromType(m_type); }
    constexpr double getViscosityTemperatureIndex() const { return getViscosityTemperatureIndexFromType(m_type); }
    constexpr double getVSSDeflectionParameter() const { return getVSSDeflectionParameterFromType(m_type); }
    constexpr double getCharge() const { return getChargeFromType(m_type); }

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

    /**
     * @brief Uses Boris Integrator to calculate updated velocity.
     * @details Lorentz force: F_L = q(E + v × B), where E - is the electric field,
                                                B - magnetic field,
                                                v - instantaneous velocity (velocity of the particle),
                                                q - charge of the particle.
                By using II-nd Newton's Law: a = F/m.
                                             a_L = F_L/m.
                                             a_L = [q(E + v × B)]/m.
     */
    void electroMagneticPush(MathVector const &magneticInduction, MathVector const &electricField, double time_step);

    /**
     * @brief Compares this Particle object to another for equality.
     * @details Two particles are considered equal if all their corresponding
     *          properties are equal.
     * @param other The Particle object to compare against.
     * @return `true` if the particles are equal, `false` otherwise.
     */
    [[nodiscard("Check of Particle equality should not be ignored to prevent logical errors")]] friend bool operator==(const Particle &lhs, const Particle &rhs)
    {
        return lhs.m_id == rhs.m_id &&
               lhs.m_type == rhs.m_type &&
               lhs.m_centre == rhs.m_centre &&
               lhs.m_velocity == rhs.m_velocity &&
               lhs.m_energy == rhs.m_energy &&
               lhs.m_bbox == rhs.m_bbox;
    }

    /**
     * @brief Compares this Particle object to another for inequality.
     * @details Two particles are considered unequal if any of their corresponding
     *          properties are not equal.
     * @param other The Particle object to compare against.
     * @return `true` if the particles are not equal, `false` otherwise.
     */
    [[nodiscard("Check of Particle inequality should not be ignored to ensure correct logic flow")]] friend bool operator!=(Particle const &lhs, Particle const &rhs) { return !(lhs == rhs); }
};

std::ostream &operator<<(std::ostream &os, Particle const &particle);

using ParticleVector = std::vector<Particle>;

/// @brief Generates a vector of particles with velocity.
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double minx = 0, double miny = 0, double minz = 0,
                                             double maxx = 100, double maxy = 100, double maxz = 100,
                                             double minvx = -100, double minvy = -100, double minvz = -100,
                                             double maxvx = 100, double maxvy = 100, double maxvz = 100);
ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double x, double y, double z,
                                             double vx, double vy, double vz);
ParticleVector createParticlesWithVelocityModule(size_t count, ParticleType type,
                                                 double x, double y, double z,
                                                 double v, double theta, double phi);

/// @brief Creates a vector of particles with energy.
ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
                                         double energy,
                                         std::array<double, 6> const &particleSourceBaseAndDirection);

#endif // !PARTICLES_HPP
