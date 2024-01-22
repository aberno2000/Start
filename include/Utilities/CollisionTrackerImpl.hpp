#ifndef COLLISIONTRACKERIMPL_HPP
#define COLLISIONTRACKERIMPL_HPP

template <IsParticle T>
constinit std::mutex CollisionTracker<T>::m_map_mutex;

template <IsParticle T>
constinit std::mutex CollisionTracker<T>::m_counter_mutex;

template <IsParticle T>
constinit size_t CollisionTracker<T>::m_counter = 0;

template <IsParticle T>
std::atomic_flag CollisionTracker<T>::m_stop_processing = ATOMIC_FLAG_INIT;

template <IsParticle T>
void CollisionTracker<T>::processSegment(size_t start_index, size_t end_index,
                                         std::unordered_map<size_t, int> &m)
{
    for (double t{}; t <= m_total_time; t += m_dt)
    {
        for (size_t i{start_index}; i < end_index; ++i)
        {
            // Exiting from thread if we need to stop processing
            if (m_stop_processing.test())
                return;

            PointD prev(m_particles.at(i).getCentre());
            m_particles.at(i).updatePosition(m_dt);
            PointD cur(m_particles.at(i).getCentre());

            for (auto const &triangle : m_mesh)
            {
                size_t id{Mesh::isRayIntersectTriangle(RayD(prev, cur), triangle)};
                if (id != -1ul)
                {
                    {
                        std::lock_guard<std::mutex> lk(m_map_mutex);
                        ++m[id];
                    }
                    {
                        std::unique_lock<std::mutex> lk(m_counter_mutex);
                        ++m_counter;

                        // Optimization 2: If counter >= count of settled particles
                        // don't need to continue calculations.
                        // @warning Here we have a little tolerance +(~1-3) counter exceeds.
                        // For example, if we have 1000 particles, counter may be from 1000 to ~1003.
                        if (m_counter >= m_particles.size())
                        {
                            m_stop_processing.test_and_set();
                            return;
                        }
                    }
                }
            }
        }
    }
}

template <IsParticle T>
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