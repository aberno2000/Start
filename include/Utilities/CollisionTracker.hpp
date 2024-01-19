#ifndef COLLISIONTRACKER_HPP
#define COLLISIONTRACKER_HPP

#include <future>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "../DataHandling/HDF5Handler.hpp"
#include "../Generators/VolumeCreator.hpp"
#include "../Geometry/Mesh.hpp"
#include "../Particles/Particles.hpp"

/**
 * @brief The `CollisionTracker` class is responsible for tracking
 *        collisions between particles and mesh elements.
 *
 * @details This class employs multi-threading to efficiently process segments of a
 *          particle collection and determine collision events with elements of a provided mesh.
 *          It operates in a concurrent environment, managing thread synchronization and safe data access.
 */
template <typename T>
class CollisionTracker final
{
    static_assert(std::is_same_v<T, ParticleGenericVector> ||
                      std::is_same_v<T, ParticleArgonVector> ||
                      std::is_same_v<T, ParticleAluminiumVector>,
                  "Template type T must be an any object of Particles");

private:
    T &m_particles;                              // Reference to a vector of particles to be processed.
    MeshParamVector const &m_mesh;               // Reference to a vector representing the mesh for collision detection.
    double m_dt;                                 // Time step for updating particle positions.
    double m_total_time;                         // Total simulation time for which collisions are tracked.
    static constinit std::mutex m_map_mutex;     // Mutex for synchronizing access to the collision map.
    static constinit std::mutex m_counter_mutex; // Mutex for synchronizing access to the counter.
    static constinit size_t m_counter;           // Count of the settled particles. Needs for optimization

    /**
     * @brief Processes a segment of the particle collection to detect collisions.
     *
     * @details This method runs in multiple threads, each processing a specified range of particles.
     *          It updates particle positions and detects collisions with mesh elements,
     *          recording collision counts.
     *
     * @param start_index The starting index in the particle vector for this segment.
     * @param end_index The ending index in the particle vector for this segment.
     * @param m Reference to the map tracking the number of collisions for each mesh element.
     */
    void processSegment(size_t start_index, size_t end_index, std::unordered_map<size_t, int> &m);

public:
    /**
     * @brief Constructs a new CollisionTracker object.
     *
     * @details Initializes the collision tracker with a given set of particles, a mesh,
     *          a time step, and a total simulation time.
     *
     * @param pgs Reference to the vector of particles.
     * @param mesh Reference to the vector of mesh elements.
     * @param dt Time step for the simulation.
     * @param total_time Total time for which the simulation is run.
     */
    CollisionTracker(T &particles, MeshParamVector const &mesh,
                     double time_step, double total_time)
        : m_particles(particles), m_mesh(mesh), m_dt(time_step), m_total_time(total_time) {}

    /**
     * @brief Tracks collisions in a concurrent manner and returns a map of collision counts.
     *
     * @details Sets up and manages multiple threads, each processing a segment of particles, to detect
     *          collisions against the mesh elements. The method aggregates collision
     *          data from all threads into a single map.
     *
     * @return std::unordered_map<size_t, int> Map with keys as mesh element IDs and values as collision counts.
     */
    std::unordered_map<size_t, int> trackCollisions();
};

#include "CollisionTrackerImpl.hpp"

#endif // !COLLISIONTRACKER_HPP
