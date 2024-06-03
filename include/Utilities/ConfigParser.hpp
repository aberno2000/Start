#ifndef CONFIGPARSER_HPP
#define CONFIGPARSER_HPP

#include <string>
#include <string_view>

#include "Utilities.hpp"

namespace ConfigParserTypes
{
    /**
     * @brief Structure to hold data for a point particle source.
     * @details This structure contains parameters defining a point particle source, including angles and coordinates.
     */
    struct point_source_t
    {
        std::string type;                        ///< Type of the particle (e.g., Ti, Al, Sn).
        size_t count{};                          ///< Number of particles.
        double energy{};                         ///< Energy of the particles in electronvolts (eV).
        double phi{};                            ///< Azimuthal angle φ.
        double theta{};                          ///< Polar (colatitude) angle θ.
        double expansionAngle{};                 ///< Expansion angle θ.
        std::array<double, 3ul> baseCoordinates; ///< Base coordinates [x, y, z].
    };

    /**
     * @brief Structure to hold data for a surface particle source.
     * @details This structure contains parameters defining a surface particle source, including type, count, energy, and coordinates.
     */
    struct surface_source_t
    {
        std::string type;                                                       ///< Type of the particle (e.g., Ti, Al, Sn).
        int count{};                                                            ///< Number of particles.
        double energy{};                                                        ///< Energy of the particles in electronvolts [eV].
        std::unordered_map<std::string, std::vector<double>> baseCoordinates{}; ///< Map of base coordinates and normals.
    };

    /**
     * @brief Structure to hold configuration data.
     * @details This structure contains parameters related to ambient conditions like
     *          temperature, pressure, volume, and energy. It also includes the types of particles
     *          involved and details about the scattering model.
     */
    struct config_data_t
    {
        /* Simulation params. */
        unsigned int num_threads{}; ///< Count of threads to processing.
        double time_step{};         ///< Simulation time step [s].
        double simtime{};           ///< Total simulation time [s].
        double temperature{};       ///< Ambient temperature in Kelvin [K].
        double pressure{};          ///< Ambient pressure in Pascals [Pa].
        ParticleType gas{};         ///< Gas particle type, e.g., N.
        std::string mshfilename;    ///< Filename of the mesh file.
        std::string model;          ///< Scattering model, e.g., HS/VHS/VSS.

        /* Particle source params. */
        std::vector<point_source_t> particleSourcePoints;     ///< Vector of point particle sources.
        std::vector<surface_source_t> particleSourceSurfaces; ///< Vector of surface particle sources.

        /* PIC and FEM params. */
        double edgeSize{};       ///< Edge size of the cubic grid that uses in PIC.
        short desiredAccuracy{}; ///< Calculation accuracy that uses in FEM to define coutn of cubature points for the linear tetrahedron.

        /* Iterative solver parameters. */
        std::string solverName;         ///< Name of the iterative solver.
        int maxIterations{};            ///< Maximum number of iterations for the solver.
        double convergenceTolerance{};  ///< Convergence tolerance for the solver.
        int verbosity{};                ///< Verbosity level of the solver.
        int outputFrequency{};          ///< Frequency of output during the solver execution.
        int numBlocks{};                ///< Number of blocks for the solver.
        int blockSize{};                ///< Block size for the solver.
        int maxRestarts{};              ///< Maximum number of restarts for the solver.
        bool flexibleGMRES{};           ///< Flag for flexible GMRES.
        std::string orthogonalization;  ///< Type of orthogonalization used in the solver.
        bool adaptiveBlockSize{};       ///< Flag for adaptive block size.
        int convergenceTestFrequency{}; ///< Frequency of convergence test during the solver execution.

        /* Boundary conditions. */
        std::vector<std::pair<std::vector<size_t>, double>> boundaryConditions; ///< Boundary conditions data.
        std::unordered_map<size_t, std::vector<double>> nodeValues;             ///< Node values.
        std::vector<size_t> nonChangeableNodes;                                 ///< Non-changeable nodes.
    };
}

using config_data_t = ConfigParserTypes::config_data_t;
using point_source_t = ConfigParserTypes::point_source_t;
using surface_source_t = ConfigParserTypes::surface_source_t;

/**
 * @brief Class for parsing and storing configuration data.
 * @details This class is responsible for parsing configuration data from a given file
 *          and storing it in a structured format. It supports retrieving various
 *          parameters related to ambient conditions, particle types, and scattering model.
 */
class ConfigParser final
{
private:
    config_data_t m_config; ///< Instance of config_data_t to store configuration.

    /// @brief Clearing out all values from the `m_config`.
    void clearConfig() { m_config = config_data_t{}; }

    /**
     * @brief Helper method to get all params from the configuration file.
     * @param config Name of the configuration file.
     */
    void getConfigData(std::string_view config);

public:
    /**
     * @brief Automatically fills configuration from the file.
     * @param config Configuration filename.
     */
    ConfigParser(std::string_view config) { getConfigData(config); }

    /// @brief Dtor. Clears out all the data members.
    ~ConfigParser() { clearConfig(); }

    /* $$$ Getters for all data members from the `config_data_t` structure. $$$ */
    constexpr unsigned int getNumThreads() const { return m_config.num_threads; }
    constexpr double getTimeStep() const { return m_config.time_step; }
    constexpr double getSimulationTime() const { return m_config.simtime; }
    constexpr double getTemperature() const { return m_config.temperature; }
    constexpr double getPressure() const { return m_config.pressure; }
    constexpr ParticleType getGas() const { return m_config.gas; }
    constexpr std::string_view getMeshFilename() const { return m_config.mshfilename.data(); }
    constexpr std::string_view getScatteringModel() const { return m_config.model.data(); }
    constexpr std::vector<point_source_t> const &getParticleSourcePoints() const { return m_config.particleSourcePoints; }
    constexpr std::vector<surface_source_t> const &getParticleSourceSurfaces() const { return m_config.particleSourceSurfaces; }
    constexpr bool isParticleSourcePoint() const { return !m_config.particleSourcePoints.empty(); }
    constexpr bool isParticleSourceSurface() const { return !m_config.particleSourceSurfaces.empty(); }
    constexpr double getEdgeSize() const { return m_config.edgeSize; }
    constexpr short getDesiredCalculationAccuracy() const { return m_config.desiredAccuracy; }
    constexpr std::string_view getSolverName() const { return m_config.solverName; }
    constexpr int getMaxIterations() const { return m_config.maxIterations; }
    constexpr double getConvergenceTolerance() const { return m_config.convergenceTolerance; }
    constexpr int getVerbosity() const { return m_config.verbosity; }
    constexpr int getOutputFrequency() const { return m_config.outputFrequency; }
    constexpr int getNumBlocks() const { return m_config.numBlocks; }
    constexpr int getBlockSize() const { return m_config.blockSize; }
    constexpr int getMaxRestarts() const { return m_config.maxRestarts; }
    constexpr bool getFlexibleGMRES() const { return m_config.flexibleGMRES; }
    constexpr std::string_view getOrthogonalization() const { return m_config.orthogonalization; }
    constexpr bool getAdaptiveBlockSize() const { return m_config.adaptiveBlockSize; }
    constexpr int getConvergenceTestFrequency() const { return m_config.convergenceTestFrequency; }
    constexpr std::vector<std::pair<std::vector<size_t>, double>> const &getBoundaryConditions() const { return m_config.boundaryConditions; }
    constexpr std::vector<size_t> const &getNonChangeableNodes() const { return m_config.nonChangeableNodes; }
};

#endif // !CONFIGPARSER_HPP
