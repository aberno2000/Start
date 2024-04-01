#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <atomic>
#include <mutex>

#include "../Geometry/Grid3D.hpp"
#include "../Particles/Particles.hpp"

/**
 * @brief The ParticleTracker class tracks the movement of particles through a tetrahedron mesh.
 * This class uses multithreading to update particle positions and track their locations within tetrahedrons
 * over time, effectively simulating particle movement in a 3D space.
 */
class ParticleTracker
{
private:
    ParticleVector &m_particles; ///< Reference to the vector of particles to be tracked.
    Grid3D &m_grid;              ///< Reference to the Grid3D object, which contains tetrahedron mesh information.
    double m_dt;                 ///< Time step for simulation.
    double m_simtime;            ///< Total simulation time.

    static std::mutex m_trackerMutex;      ///< Mutex for synchronizing access to the particle tracker map.
    static std::mutex m_outputStreamMutex; ///< Mutex for synchronizing output streams.

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

public:
    ParticleTracker(ParticleVector &particles, Grid3D &grid, double dt, double simtime)
        : m_particles(particles), m_grid(grid), m_dt(dt), m_simtime(simtime) {}

    /**
     * @brief Runs the particle tracking simulation over the specified time frame using multiple threads.
     * @param num_threads Number of threads to use for the simulation.
     * @return A map where the key is the tetrahedron ID and the value is a vector of particles within that tetrahedron.
     */
    void trackParticles(unsigned int num_threads = std::thread::hardware_concurrency());
};

#endif // !PARTICLETRACKER_HPP
