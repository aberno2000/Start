#include <algorithm>
#include <execution>
#include <sstream>

#include "../include/ParticleTracker.hpp"

std::mutex ParticleTracker::m_collisionMutex;
std::mutex ParticleTracker::m_PICMutex;
std::atomic<size_t> ParticleTracker::m_collisionCounter;
std::atomic_flag ParticleTracker::m_stopProcessing = ATOMIC_FLAG_INIT;

bool ParticleTracker::isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam)
{
    try
    {
        CGAL::Oriented_side oriented_side{std::get<1>(meshParam).oriented_side(particle.getCentre())};
        if (oriented_side == CGAL::ON_POSITIVE_SIDE)
            return true;
        else if (oriented_side == CGAL::ON_NEGATIVE_SIDE)
            return false;
        else
            // TODO: Correctly handle case when particle is on boundary of tetrahedron.
            return true;
    }
    catch (std::exception const &e)
    {
        ERRMSG(util::stringify(e.what(), ". Returning `false` as default result of checking is the particle inside tetrahedron"));
    }
    catch (...)
    {
        std::stringstream ss, ss2;
        ss << particle;
        ss2 << meshParam;

        ERRMSG(util::stringify("Something went wrong while checking is the particle[",
                               particle.getId(), "] with coordinates: [", ss.str(),
                               "] inside the tetrahedron[", std::get<0>(meshParam), "]: ", ss2.str(),
                               ". Returning `false` as default result of checking is the particle inside tetrahedron"));
    }
    return false;
}

void ParticleTracker::processSegment(size_t start_index, size_t end_index, AABB_Tree_Triangle const &tree)
{
    Particle gasParticle(m_configObj.getGas());
    std::unordered_map<size_t, int> localCollisionMap;
    std::map<size_t, ParticleVector> localParticlesInCell;

    try
    {
        double dt{m_configObj.getTimeStep()};
        for (double t{}; t <= m_configObj.getSimulationTime() && !m_stopProcessing.test(); t += dt)
        {
            std::for_each(std::execution::par, m_particles.begin() + start_index, m_particles.begin() + end_index,
                          [&](Particle &p)
                          {
                              // At the initial time moment just move the particles with initial specified velocities.
                              if (t == 0.0)
                                  p.updatePosition(dt);
                              else
                              {
                                  // Collision detection part.
                                  if (m_collisionCounter.load() >= m_particles.size())
                                      return;

                                  Point prev(p.getCentre());
                                  if (p.colide(gasParticle, m_gasConcentration, m_configObj.getScatteringModel(), dt))
                                  {
                                      // TODO: Assembly GSM, solve Ax=b.

                                      // 1) Calculate electric field for each tetrahedron
                                      // 2) Set magnetic field (temporary) by default with vector (1, 1, 1)
                                      // 3) Do EM push to update the velocity
                                      // 4) Move particle

                                      p.updatePosition(dt);
                                  }

                                  Ray ray(prev, p.getCentre());
                                  if (!ray.is_degenerate())
                                  {
                                      auto intersection{tree.first_intersection(ray)};
                                      if (intersection)
                                      {
                                          auto triangle{boost::get<Triangle>(*intersection->second)};
                                          if (!triangle.is_degenerate())
                                          {
                                              auto matchedIt{std::ranges::find_if(m_mesh, [triangle](auto const &el)
                                                                                  { return triangle == std::get<1>(el); })};
                                              if (matchedIt != m_mesh.cend())
                                              {
                                                  size_t id = Mesh::isRayIntersectTriangle(ray, *matchedIt);
                                                  if (id != -1ul)
                                                  {
                                                      std::lock_guard<std::mutex> lk(m_collisionMutex);
                                                      localCollisionMap[id]++;
                                                      m_collisionCounter.fetch_add(1);

                                                      if (m_collisionCounter.load() >= m_particles.size())
                                                      {
                                                          m_stopProcessing.test_and_set();
                                                          return;
                                                      }
                                                  }
                                              }
                                          }
                                      }
                                  }

                                  // PIC tracking part.
                                  auto meshParams{m_grid.getTetrahedronsByGridIndex(m_grid.getGridIndexByPosition(p.getCentre()))};
                                  for (auto const &meshParam : meshParams)
                                  {
                                      if (isParticleInsideTetrahedron(p, meshParam))
                                      {
                                          std::lock_guard<std::mutex> lock(m_PICMutex);
                                          localParticlesInCell[std::get<0>(meshParam)].emplace_back(p);
                                      }
                                  }
                              }
                          });

            // At the end of each time step, merge thread-local data into shared structures.
            {
                std::lock_guard<std::mutex> CollisionTrackerLock(m_collisionMutex);
                for (const auto &[id, count] : localCollisionMap)
                    m_collisionMap[id] += count;
            }
            {
                std::lock_guard<std::mutex> ParticleInCellLock(m_PICMutex);
                for (const auto &[tetraId, particles] : localParticlesInCell)
                    m_particlesInCell.at(t).at(tetraId).insert(m_particlesInCell.at(t).at(tetraId).end(), particles.begin(), particles.end());
            }
        }
    }
    catch (std::exception const &e)
    {
        ERRMSG(e.what());
    }
    catch (...)
    {
        ERRMSG("Something went wrong while executing the simulation");
    }
}

void ParticleTracker::runSimulation(unsigned int num_threads)
{
    if (auto curThreads{std::thread::hardware_concurrency()}; curThreads < num_threads)
        throw std::runtime_error("The number of threads requested (" + std::to_string(num_threads) +
                                 ") exceeds the number of hardware threads supported by the system (" +
                                 std::to_string(curThreads) +
                                 "). Please reduce the number of threads or run on a system with more resources.");

    // Initialize AABB for the surface mesh.
    auto tree{constructAABBTreeFromMeshParams(m_mesh)};
    if (!tree)
    {
        ERRMSG("Failed to fill AABB tree for 2D mesh. Exiting...");
        std::exit(EXIT_FAILURE);
    }

    // Reset atomic and flag variables
    m_collisionCounter = 0;
    m_stopProcessing.clear();

    // Calculate the number of threads and segment size
    size_t particles_per_thread{m_particles.size() / num_threads};

    // Vector to hold futures from async operations
    std::vector<std::future<void>> futures;
    size_t start_index{};

    for (unsigned int i{}; i < num_threads; ++i)
    {
        size_t end_index{(i == num_threads - 1) ? m_particles.size() : start_index + particles_per_thread};

        // Launch a thread to process each segment.
        futures.emplace_back(std::async(std::launch::async, [this, start_index, end_index, &tree]()
                                        { this->processSegment(start_index, end_index, *tree); }));
        start_index = end_index;
    }

    // Wait for all threads to complete their tasks.
    for (auto &future : futures)
        future.get();
}
