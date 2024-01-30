#ifndef CONCENTRATIONCALCULATOR_HPP
#define CONCENTRATIONCALCULATOR_HPP

#include <string>
#include <string_view>

#include "Constants.hpp"

using namespace constants;
using namespace particle_types;

#define BAD_VOLUME -8.0
#define BAD_PRESSURE -7.0
#define BAD_TEMPERATURE -6.0
#define BAD_ENERGY -5.0
#define BAD_MODEL -4.0
#define UNKNOWN_PARTICLES -3.0
#define BAD_PARTICLES_FORMAT -2.0
#define BAD_FILE -1.0
#define EMPTY_STR 0.0
#define STATUS_OK 1.0

class ConcentrationCalculator final
{
private:
    static double temperature;
    static double pressure;
    static double volume;
    static double energy;
    static ParticleType projective;
    static ParticleType gas;
    static std::string mshfilename;
    static std::string model;

    /// @brief Helper method to parse and define particle type by string.
    static ParticleType getParticleTypeFromStrRepresentation(std::string particle);

    /// @brief Helper method to get all params from the configuration file.
    static double getParams(std::string_view config);

public:
    /**
     * @brief Calculates concentration using configuration file.
     * @param config Name of the configuration file.
     *
     * @details Configuration file:
     * T: <value> (Tempreature in [K]).
     * P: <value> (Preassure in [Pa]).
     * V/msh: <value>/<string> (Volume in [m^3]/name of the file with tetrahedron mesh from GMSH).
     * Particles: <projective> <target>: (particle) (gas): Example: Al Ar.
     * Energy: <value> [eV].
     * Model: HS/VHS/VSS.
     *
     * @example
     * T: 300
     * P: 10000
     * V/msh: 95.42
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
    static double calculateConcentration(std::string_view config);
};

#endif // !CONCENTRATIONCALCULATOR_HPP
