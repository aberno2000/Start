#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <mutex>

#include "../Particles/Particles.hpp"
#include "Grid3D.hpp"

/**
 * @brief The ParticleTracker class tracks the movement of particles through a tetrahedron mesh.
 * This class uses multithreading to update particle positions and track their locations within tetrahedrons
 * over time, effectively simulating particle movement in a 3D space.
 */
class ParticleTracker final
{
private:
    ParticleVector &m_particles; ///< Reference to the vector of particles to be tracked.
    Grid3D &m_grid;              ///< Reference to the Grid3D object, which contains tetrahedron mesh information.
    double m_dt;                 ///< Time step for simulation.
    double m_simtime;            ///< Total simulation time.

    /* (Time step | Tetrahedron ID | Particles inside) */
    std::map<double, std::map<size_t, ParticleVector>> m_particlesInCell; ///< Variable to store particles in each time step with known tetrahedra ID.

    /* (Time step | Tetrahedron ID | Charge in coulumbs) */
    std::map<double, std::map<size_t, double>> m_chargeDensityMap; ///< Charge map: charge in coulumbs for all tetrahedra and for all time steps.

    /* (Time interval ID | time value) */
    std::map<int, double> m_timeMap; ///< Time interval map.

    static std::mutex m_trackerMutex; ///< Mutex for synchronizing access to the particle tracker map.
    static std::mutex m_PICMutex;     ///< Mutex for synchronizing adding values to the `m_particlesInCell`.

    /// @brief Fills time interval map.
    void fillTimeMap();

    /**
     * @brief Checker for point inside the tetrahedron.
     * @param point `Point_3` from CGAL.
     * @param tetrahedron `Tetrahedron_3` from CGAL.
     * @return `true` if point within the tetrahedron, otherwise `false`.
     */
    bool isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam);

    /**
     * @brief Updates particle positions and tracks their locations for a segment of the total simulation time.
     * @param start_time Starting time for the segment.
     * @param end_time Ending time for the segment.
     */
    void processSegment(double start_time, double end_time);

    /**
     * @brief Runs the particle tracking simulation over the specified time frame using multiple threads.
     * @param num_threads Number of threads to use for the simulation.
     * @return A map where the key is the tetrahedron ID and the value is a vector of particles within that tetrahedron.
     */
    void trackParticles(unsigned int num_threads = std::thread::hardware_concurrency());

    /// @brief Fills charge map with according data.
    void calculateChargeDensityMap();

public:
    ParticleTracker(ParticleVector &particles, Grid3D &grid,
                    double dt, double simtime,
                    unsigned int num_threads = std::thread::hardware_concurrency());

    /// @brief Prints all the data from the particle in cell storage: in what time where were particles (in which tetrahedra).
    void printPIC() const;

    /// @brief Prints all the data from the charge map.
    void printChargeDensityMap() const;

    /* Getters. */
    constexpr double getTimeStep() const { return m_dt; }
    constexpr double getSimulationTime() const { return m_simtime; }
    constexpr std::map<double, std::map<size_t, ParticleVector>> const &getParticlesInCell() const { return m_particlesInCell; }
    constexpr std::map<double, std::map<size_t, double>> const &getChargeDensityMap() const { return m_chargeDensityMap; }
    constexpr std::map<int, double> const &getTimeIntervalMap() const { return m_timeMap; }
    size_t getTimeIntervals() const { return m_timeMap.size(); }
    double getTimeFromInterval(int time_interval) const { return m_timeMap.at(time_interval); }

    /* Cleaners. */
    void clearParticlesInCell() { m_particlesInCell.clear(); }
    void clearChargeDensityMap() { m_chargeDensityMap.clear(); }

    /* Getters on emptiness. */
    bool isParticlesIncellEmpty() const { return m_particlesInCell.empty(); }
    bool isChargeDensityMapEmpty() const { return m_chargeDensityMap.empty(); }

    /* Getters for specified time step. */
    std::map<size_t, ParticleVector> getParticlesInCell(int time_interval) const;
    std::map<size_t, double> getChargeDensityMap(int time_interval) const;
};

#endif // !PARTICLETRACKER_HPP
