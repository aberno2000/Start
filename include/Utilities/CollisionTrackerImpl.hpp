#ifndef COLLISIONTRACKERIMPL_HPP
#define COLLISIONTRACKERIMPL_HPP

#include <algorithm>
#include <execution>

template <IsParticleVector T>
constinit std::mutex CollisionTracker<T>::m_map_mutex;

template <IsParticleVector T>
std::atomic<size_t> CollisionTracker<T>::m_counter = 0ul;

template <IsParticleVector T>
std::atomic_flag CollisionTracker<T>::m_stop_processing = ATOMIC_FLAG_INIT;

template <IsParticleVector T>
void CollisionTracker<T>::processSegment(size_t start_index, size_t end_index,
                                         std::unordered_map<size_t, int> &m)
{
    for (double t{}; t <= m_total_time && !m_stop_processing.test(); t += m_dt)
    {
        std::for_each(std::execution::par,
                      m_particles.begin() + start_index,
                      m_particles.begin() + end_index,
                      [&](auto &p)
                      {
                          // Check each counter iteration
                          if (m_counter.load() >= m_particles.size())
                              return;

                          Point3 prev(p.getCentre());
                          p.updatePosition(m_dt);
                          Ray3 ray(prev, p.getCentre());

                          for (auto const &triangle : m_mesh)
                          {
                              size_t id{Mesh::isRayIntersectTriangle(ray, triangle)};
                              if (id != -1ul)
                              {
                                  std::lock_guard<std::mutex> lk(m_map_mutex);
                                  ++m[id];
                                  m_counter.fetch_add(1);

                                  if (m_counter.load() >= m_particles.size())
                                  {
                                      m_stop_processing.test_and_set();
                                      return;
                                  }
                              }
                          }
                      });
    }
}

template <IsParticleVector T>
std::unordered_map<size_t, int> CollisionTracker<T>::trackCollisions()
{
    std::unordered_map<size_t, int> m;

    // Number of concurrent threads supported by the implementation
    size_t num_threads{std::thread::hardware_concurrency()};
    std::vector<std::future<void>> futures;

    // Separate on segments
    size_t particles_per_thread{m_particles.size() / num_threads},
        start_index{};

    // Create threads and assign each a segment of particles to process
    for (size_t i{}; i < num_threads; ++i)
    {
        size_t end_index{(i == num_threads - 1) ? m_particles.size() : start_index + particles_per_thread};
        futures.emplace_back(std::async(std::launch::async, [this, start_index, end_index, &m]()
                                        { this->processSegment(start_index, end_index, m); }));
        start_index = end_index;
    }

    // Wait for all threads to complete their work
    for (auto &f : futures)
        f.get();

    return m;
}

#endif // !COLLISIONTRACKERIMPL_HPP