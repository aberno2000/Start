#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <atomic>
#include <future>
#include <map>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "DataHandling/HDF5Handler.hpp"
#include "Generators/VolumeCreator.hpp"
#include "Geometry/Mesh.hpp"
#include "ParticleInCell/Grid3D.hpp"
#include "Particles/Particles.hpp"
#include "Utilities/ConfigParser.hpp"

/**
 * @brief The ParticleTracker class tracks the movement and collisions of particles through a 3D mesh.
 *        It uses multithreading to update particle positions and detect collisions with mesh surfaces.
 */
class ParticleTracker final
{
private:
    ParticleVector &m_particles;           ///< Reference to the vector of particles to be tracked.
    MeshTriangleParamVector const &m_mesh; ///< Reference to the mesh for collision detection.
    Grid3D &m_grid;                        ///< Reference to the Grid3D object for PIC simulations.
    ConfigParser const &m_configObj;       ///< Configuration object for simulation parameters.
    double m_dt;                           ///< Time step for simulation.
    double m_simtime;                      ///< Total simulation time.
    double m_gasConcentration;             ///< Gas concentration in the volume.

    // Maps and storage for collision and PIC data.
    std::unordered_map<size_t, int> m_collisionMap;                       ///< Map of collision counts.
    std::map<double, std::map<size_t, ParticleVector>> m_particlesInCell; ///< Particles in each cell by time step.
    std::map<double, std::map<size_t, double>> m_chargeDensityMap;        ///< Charge density map by time step.

    // Synchronization primitives.
    static std::mutex m_collisionMutex;            ///< Mutex for collision data access.
    static std::mutex m_PICMutex;                  ///< Mutex for PIC data access.
    static std::atomic<size_t> m_collisionCounter; ///< Count of detected collisions.
    static std::atomic_flag m_stopProcessing;      ///< Flag to stop processing threads.

    /**
     * @brief Checker for point inside the tetrahedron.
     * @param point `Point_3` from CGAL.
     * @param tetrahedron `Tetrahedron_3` from CGAL.
     * @return `true` if point within the tetrahedron, otherwise `false`.
     */
    bool isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam);

    /**
     * @brief Process a segment of particles for both collision detection and PIC simulation.
     * @param start_index Starting index in the particle vector for this segment.
     * @param end_index Ending index in the particle vector for this segment.
     * @param tree AABB tree for the mesh.
     */
    void processSegment(size_t start_index, size_t end_index, AABB_Tree_Triangle const &tree);

public:
    /**
     * @brief Constructs a new ParticleTracker object.
     * @param particles Reference to the vector of particles.
     * @param mesh Reference to the vector of mesh elements for collision detection.
     * @param grid Reference to the Grid3D object for PIC simulation.
     * @param configObj Configuration object for simulation parameters.
     * @param dt Time step for the simulation.
     * @param simtime Total simulation time.
     * @param gasConcentration Concentration of the gas in the volume.
     */
    ParticleTracker(ParticleVector &particles, MeshTriangleParamVector const &mesh, Grid3D &grid,
                    ConfigParser const &configObj, double dt, double simtime, double gasConcentration)
        : m_particles(particles), m_mesh(mesh), m_grid(grid), m_configObj(configObj),
          m_dt(dt), m_simtime(simtime), m_gasConcentration(gasConcentration) {}

    /**
     * @brief Runs the simulation using multiple threads to update positions and track collisions.
     * @param num_threads Number of threads to execute (default: $(nproc) value).
     */
    void runSimulation(unsigned int num_threads = std::thread::hardware_concurrency());

    /**
     * @brief Prints all the data from the collision map and PIC storage.
     */
    void printSimulationResults() const;
};

#endif // !PARTICLETRACKER_HPP
