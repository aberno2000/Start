#ifndef COLLISIONTRACKERIMPL_HPP
#define COLLISIONTRACKERIMPL_HPP

template <typename T>
constinit std::mutex CollisionTracker<T>::m_map_mutex;

template <typename T>
constinit std::mutex CollisionTracker<T>::m_counter_mutex;

template <typename T>
constinit size_t CollisionTracker<T>::m_counter = 0;

template <typename T>
void CollisionTracker<T>::processSegment(size_t start_index, size_t end_index,
                                         std::unordered_map<size_t, int> &m)
{
    for (double t{}; t <= m_total_time; t += m_dt)
    {
        for (size_t i{start_index}; i < end_index; ++i)
        {
            PointD prev(m_particles[i].getCentre());
            m_particles[i].updatePosition(m_dt);
            PointD cur(m_particles[i].getCentre());

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
                        std::lock_guard<std::mutex> lk(m_counter_mutex);
                        ++m_counter;
                    }
                    break;
                }
            }
        }
        {
            // Optimization 2: If counter == count of passed particles
            // don't need to continue calculations
            std::lock_guard<std::mutex> lk(m_counter_mutex);
            if (m_counter == m_particles.size())
                return;
        }
    }
}

template <typename T>
std::unordered_map<size_t, int> CollisionTracker<T>::trackCollisions()
{
    std::unordered_map<size_t, int> m;

    // Number of concurrent threads supported by the implementation
    size_t num_threads{std::thread::hardware_concurrency()};
    std::vector<std::future<void>> futures;

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
