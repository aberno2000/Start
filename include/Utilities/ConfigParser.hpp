#ifndef CONFIGPARSER_HPP
#define CONFIGPARSER_HPP

#include <string>
#include <string_view>

#include "Utilities.hpp"

class ConfigParser final
{
private:
    struct config_data_t
    {
        // Ambient conditions.
        double temperature{}; // [K]
        double pressure{};    // [Pa]
        double volume{};      // [m^3]
        double energy{};      // [eV]

        // Particle types.
        ParticleType projective{}; // @example Au
        ParticleType gas{};        // @example N

        // Filename with mesh.
        std::string mshfilename;

        // Scattering model.
        std::string model; // HS/VHS/VSS
    } m_config;

    /// @brief Clearing out all values from the `m_config`.
    void clearConfig();

    /**
     * @brief Helper method to get all params from the configuration file.
     * @param config Name of the configuration file.
     *
     * @details Configuration file:
     * T: <value> (Tempreature in [K]).
     * P: <value> (Preassure in [Pa]).
     * V: <value>/<string> (Volume in [m^3]/name of the file with tetrahedron mesh from GMSH).
     * Particles: <projective> <target>: (particle) (gas): Example: Al Ar.
     * Energy: <value> [eV].
     * Model: HS/VHS/VSS.
     *
     * @example
     * T: 300
     * P: 10000
     * V: 95.42
     * Particles: Al Ar
     * Energy: 25
     * Model: HS
     *
     * @return Concentration calculated from the specified conditions in [N] (count of particles in V).
     * `EMPTY_STR` constant (=0.0) if `config` is empty.
     * `BAD_FILE` constant (=-1.0) if something wrong with the file.
     * `BAD_PARTICLES_FORMAT` constant (=-2.0) if particles format is incorrect.
     * `UNKNOWN_PARTICLES` constant (=-3.0) if input particles aren't correspond to known.
     * `BAD_MODEL` constant (=-4.0) if model is unknown.
     * `BAD_ENERGY` constant (=-5.0) if energy is equals to `0.0` or negative.
     * `BAD_TEMPERATURE` constant (=-6.0) if temperature is equals to `0.0` or negative.
     * `BAD_PRESSURE` constant (=-7.0) if pressure is negative.
     * `BAD_VOLUME` constant (=-8.0) if volume is <= 0.0.
     */
    double getConfigData(std::string_view config);

public:
    /**
     * @brief Automatically fills configuration from the file.
     * @param config Configuration filename.
     */
    ConfigParser(std::string_view config);

    /* $$$ Getters for all data members from the `config_data_t` structure. $$$ */
    constexpr config_data_t const &getConfigurations() const _GLIBCXX_NOEXCEPT { return m_config; }
    constexpr double getTemperature() const _GLIBCXX_NOEXCEPT { return m_config.temperature; }
    constexpr double getPressure() const _GLIBCXX_NOEXCEPT { return m_config.pressure; }
    constexpr double getVolume() const _GLIBCXX_NOEXCEPT { return m_config.volume; }
    constexpr double getEnergy() const _GLIBCXX_NOEXCEPT { return m_config.energy; }
    constexpr ParticleType getProjective() const _GLIBCXX_NOEXCEPT { return m_config.projective; }
    constexpr ParticleType getGas() const _GLIBCXX_NOEXCEPT { return m_config.gas; }
    constexpr std::string getMeshFilename() const _GLIBCXX_NOEXCEPT { return m_config.mshfilename; }
    constexpr std::string getScatteringModel() const _GLIBCXX_NOEXCEPT { return m_config.model; }
};

#endif // !CONFIGPARSER_HPP
