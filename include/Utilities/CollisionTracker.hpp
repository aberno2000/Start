#ifndef COLLISIONTRACKER_HPP
#define COLLISIONTRACKER_HPP

#include <atomic>
#include <future>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <vector>

#include "../DataHandling/HDF5Handler.hpp"
#include "../Generators/VolumeCreator.hpp"
#include "../Geometry/Mesh.hpp"
#include "../Particles/Particle.hpp"
#include "ConfigParser.hpp"

/**
 * @brief The `CollisionTracker` class is responsible for tracking
 *        collisions between particles and mesh elements.
 *
 * @details This class employs multi-threading to efficiently process segments of a
 *          particle collection and determine collision events with elements of a provided mesh.
 *          It operates in a concurrent environment, managing thread synchronization and safe data access.
 */
class CollisionTracker
{
private:
	ParticleVector &m_particles;			   // Reference to a vector of particles to be processed.
	MeshTriangleParamVector const &m_mesh;	   // Reference to a vector representing the mesh for collision detection.
	ConfigParser const &m_configObj;		   // `ConfigParser` object that keeps all necessary simulation parameters.
	double m_gasConcentration;				   // Concentration of the gas.
	static std::mutex m_map_mutex;			   // Mutex for synchronizing access to the collision map.
	static std::atomic<size_t> m_counter;	   // Count of the settled particles. Needs for optimization.
	static std::atomic_flag m_stop_processing; // Flag-checker for condition (counter >= size of particles).

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
	 * @param tree AABB tree for the mesh.
	 */
	void processSegment(size_t start_index, size_t end_index,
						std::unordered_map<size_t, int> &m, AABB_Tree_Triangle const &tree);

public:
	/**
	 * @brief Constructs a new CollisionTracker object.
	 *
	 * @details Initializes the collision tracker with a given set of particles, a mesh,
	 *          a time step, and a total simulation time.
	 *
	 * @param particles Reference to the vector of particles.
	 * @param mesh Reference to the vector of mesh elements.
	 * @param configObj Config object to get all necessary simulation params.
	 * @param gasConcentration Concentration of the gas in the volume.
	 */
	CollisionTracker(ParticleVector &particles, MeshTriangleParamVector const &mesh,
					 ConfigParser const &configObj, double gasConcentration)
		: m_particles(particles), m_mesh(mesh), m_configObj(configObj),
		  m_gasConcentration(gasConcentration) {}
	CollisionTracker(ParticleVector &particles, MeshTriangleParamVector &&mesh,
					 ConfigParser const &configObj, double gasConcentration)
		: m_particles(particles), m_mesh(std::move(mesh)),
		  m_configObj(configObj), m_gasConcentration(gasConcentration) {}

	/**
	 * @brief Tracks collisions in a concurrent manner and returns a map of collision counts.
	 *
	 * @details Sets up and manages multiple threads, each processing a segment of particles, to detect
	 *          collisions against the mesh elements. The method aggregates collision
	 *          data from all threads into a single map.
	 * @param num_threads Number of threads to execute (default: $(nproc) value).
	 *
	 * @return std::unordered_map<size_t, int> Map with keys as mesh element IDs and values as collision counts.
	 */
	std::unordered_map<size_t, int> trackCollisions(unsigned int num_threads = std::thread::hardware_concurrency());
};

#endif // !COLLISIONTRACKER_HPP
