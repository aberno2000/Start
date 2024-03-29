#include <algorithm>
#include <execution>
#include <ranges>

#include "../include/Utilities/CollisionTracker.hpp"
#include "../include/Utilities/Utilities.hpp"

std::mutex CollisionTracker::m_map_mutex;
std::atomic<size_t> CollisionTracker::m_counter = 0ul;
std::atomic_flag CollisionTracker::m_stop_processing = ATOMIC_FLAG_INIT;

void CollisionTracker::processSegment(size_t start_index, size_t end_index,
                                      std::unordered_map<size_t, int> &m, AABB_Tree_Triangle const &tree)
{
    Particle gasParticle(m_configObj.getGas());
    for (double t{};
         t <= m_configObj.getSimulationTime() && !m_stop_processing.test();
         t += m_configObj.getTimeStep())
    {
        std::for_each(std::execution::par,
                      m_particles.begin() + start_index,
                      m_particles.begin() + end_index,
                      [&](auto &p)
                      {
                          // Check each counter iteration
                          if (m_counter.load() >= m_particles.size())
                              return;

                          Point prev(p.getCentre());
                          if (p.colide(gasParticle, m_gasConcentration,
                                       m_configObj.getScatteringModel(),
                                       m_configObj.getTimeStep()))
                              p.updatePosition(m_configObj.getTimeStep());
                          Ray ray(prev, p.getCentre());

                          // Check ray on degeneracy
                          if (not ray.is_degenerate())
                          {
                              // Check intersection of ray with mesh
                              auto intersection{tree.first_intersection(ray)};
                              if (intersection)
                              {
                                  // Getting triangle object
                                  auto triangle{boost::get<Triangle>(*intersection->second)};

                                  // Check if some of sides of angles in the triangle <= 0 (check on degeneracy)
                                  if (not triangle.is_degenerate())
                                  {
                                      // Finding matching triangle in `m_mesh`
                                      auto matchedIt{std::ranges::find_if(m_mesh, [triangle](auto const &el)
                                                                          { return triangle == std::get<1>(el); })};
                                      if (matchedIt != m_mesh.cend())
                                      {
                                          // If we have positive result in previous steps -> next step to get the ID
                                          // will be 100% successfull
                                          // Getting the ID
                                          size_t id{Mesh::isRayIntersectTriangle(ray, *matchedIt)};
                                          if (id != -1ul)
                                          {
                                              /* Critical section - map is shared object */
                                              std::lock_guard<std::mutex> lk(m_map_mutex);
                                              ++m[id];
                                              m_counter.fetch_add(1);

                                              // If counter of setteled particles >= count of particles -> stop processing
                                              if (m_counter.load() >= m_particles.size())
                                              {
                                                  m_stop_processing.test_and_set();
                                                  return;
                                              }
                                          }
                                      }
                                  }
                              }
                          }
                      });
    }
}

std::unordered_map<size_t, int> CollisionTracker::trackCollisions(unsigned int num_threads)
{
    std::unordered_map<size_t, int> m;

    // Number of concurrent threads supported by the implementation
    std::vector<std::future<void>> futures;

    // Separate on segments
    size_t particles_per_thread{m_particles.size() / num_threads},
        start_index{};

    // Initializing AABB-tree
    auto tree{constructAABBTreeFromMeshParams(m_mesh)};
    if (!tree)
    {
        ERRMSG("Failed to fill AABB tree for 2D mesh. Exiting...");
        std::exit(EXIT_FAILURE);
    }

    // Create threads and assign each a segment of particles to process
    for (size_t i{}; i < num_threads; ++i)
    {
        size_t end_index{(i == num_threads - 1) ? m_particles.size() : start_index + particles_per_thread};
        futures.emplace_back(std::async(std::launch::async, [this, start_index, end_index, &m, &tree]()
                                        { this->processSegment(start_index, end_index, m, *tree); }));
        start_index = end_index;
    }

    // Wait for all threads to complete their work
    for (auto &f : futures)
        f.get();

    return m;
}
