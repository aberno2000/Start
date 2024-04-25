#include <algorithm>
#include <execution>
#include <future>

#include "../include/ParticleInCell/ParticleTracker.hpp"

std::mutex ParticleTracker::m_trackerMutex;
std::mutex ParticleTracker::m_PICMutex;

bool ParticleTracker::isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam)
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

void ParticleTracker::processSegment(double start_time, double end_time)
{
    for (double t{start_time}; t <= end_time; t += m_dt)
    {
        std::map<size_t, ParticleVector> tempTracker;
        std::for_each(std::execution::par, m_particles.begin(), m_particles.end(), [&](Particle &pt)
                      {
            if (t != 0.0)
                pt.updatePosition(m_dt);

            // Determine which tetrahedrons the particle may intersect based on its grid index
            auto meshParams{m_grid.getTetrahedronsByGridIndex(m_grid.getGridIndexByPosition(pt.getCentre()))};
            for (auto const &meshParam : meshParams) {
                if (isParticleInsideTetrahedron(pt, meshParam))
                {
                    std::lock_guard<std::mutex> lock(m_trackerMutex); // Protect access to tempTracker.
                    tempTracker[std::get<0>(meshParam)].emplace_back(pt);
                }
            } });

        {
            std::lock_guard<std::mutex> lock(m_PICMutex);
            m_particles_in_cell.insert({start_time, tempTracker});
        }
    }
}

void ParticleTracker::trackParticles(unsigned int num_threads)
{
    std::vector<std::future<void>> futures;
    double segment_length{m_simtime / num_threads};

    for (unsigned int i{}; i < num_threads; ++i)
    {
        double start_time{i * segment_length};
        double end_time{(i + 1) * segment_length};

        futures.emplace_back(std::async(std::launch::async, [this, start_time, end_time]()
                                        { this->processSegment(start_time, end_time); }));
    }

    for (auto &future : futures)
        future.get();
}

void ParticleTracker::print() const
{
    if (m_particles_in_cell.empty())
    {
        WARNINGMSG("Nothing to print. Data storage for the particles in cell is empty");
        return;
    }

    for (auto const &[dt, PICs] : m_particles_in_cell)
    {
        size_t count{};
        std::cout << std::format("\033[1;34mTime {}\n\033[0m", dt);
        for (auto const &[tetrId, particles] : PICs)
        {
            count += particles.size();
            std::cout << std::format("Tetrahedron[{}]: ", tetrId);
            for (auto const &pt : particles)
                std::cout << pt.getId() << ' ';
            std::endl(std::cout);
        }
        std::cout << "Count of particles: " << count << '\n';
    }
}
