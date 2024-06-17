#include <algorithm>
#include <execution>
#include <future>

#include "../include/ParticleInCell/ParticleInCellTracker.hpp"

std::mutex ParticleInCellTracker::m_trackerMutex;
std::mutex ParticleInCellTracker::m_PICMutex;

void ParticleInCellTracker::fillTimeMap()
{
    int timeID{};
    if (!m_chargeDensityMap.empty())
        for (auto const &entry : m_chargeDensityMap)
            m_timeMap.insert({timeID++, entry.first});
}

bool ParticleInCellTracker::isParticleInsideTetrahedron(Particle const &particle, Tetrahedron const &tetrahedron)
{
    CGAL::Oriented_side oriented_side{tetrahedron.oriented_side(particle.getCentre())};
    if (oriented_side == CGAL::ON_POSITIVE_SIDE)
        return true;
    else if (oriented_side == CGAL::ON_NEGATIVE_SIDE)
        return false;
    else
        return true;
}

void ParticleInCellTracker::processSegment(double start_time, double end_time)
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
                if (isParticleInsideTetrahedron(pt, meshParam.tetrahedron))
                {
                    std::lock_guard<std::mutex> lock(m_trackerMutex); // Protect access to tempTracker.
                    tempTracker[meshParam.globalTetraId].emplace_back(pt);
                }
            } });

        {
            std::lock_guard<std::mutex> lock(m_PICMutex);
            m_particlesInCell.insert({start_time, tempTracker});
        }
    }
}

void ParticleInCellTracker::trackParticles(unsigned int num_threads)
{
    if (auto curThreads{std::thread::hardware_concurrency()}; curThreads < num_threads)
        throw std::runtime_error("The number of threads requested (" + std::to_string(num_threads) +
                                 ") exceeds the number of hardware threads supported by the system (" +
                                 std::to_string(curThreads) +
                                 "). Please reduce the number of threads or run on a system with more resources.");

    std::vector<std::future<void>> futures;
    double segment_length{m_simtime / num_threads};
    for (unsigned int i{}; i < num_threads; ++i)
    {
        double start_time{i * segment_length},
            end_time{(i + 1) * segment_length};

        futures.emplace_back(std::async(std::launch::async, [this, start_time, end_time]()
                                        { this->processSegment(start_time, end_time); }));
    }

    for (auto &future : futures)
        future.get();
}

void ParticleInCellTracker::calculateChargeDensityMap()
{
    if (!m_chargeDensityMap.empty())
        m_chargeDensityMap.clear();

    for (auto const &[dt, PICs] : m_particlesInCell)
    {
        std::map<size_t, double> tempMap;
        for (auto const &[tetrId, particles] : PICs)
        {
            tempMap.insert({tetrId,
                            (std::accumulate(particles.cbegin(), particles.cend(), 0.0, [](double sum, auto const &particle)
                                             { return sum + particle.getCharge(); })) / 1}); // Dummy volume - 1.
        }
        m_chargeDensityMap.insert({dt, tempMap});
    }
}

ParticleInCellTracker::ParticleInCellTracker(ParticleVector &particles, Grid3D &grid,
                                             double dt, double simtime,
                                             unsigned int num_threads)
    : m_particles(particles), m_grid(grid), m_dt(dt), m_simtime(simtime)
{
    trackParticles(num_threads);
    calculateChargeDensityMap();
    fillTimeMap();
}

void ParticleInCellTracker::printParticlesMap() const
{
    if (m_particlesInCell.empty())
    {
        WARNINGMSG("Nothing to print. Data storage for the particles in cell is empty");
        return;
    }

    for (auto const &[dt, PICs] : m_particlesInCell)
    {
        size_t count{};
        std::cout << std::format("\033[1;34mTime {} s\n\033[0m", dt);
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

void ParticleInCellTracker::printChargeDensityMap() const
{
    if (m_chargeDensityMap.empty())
    {
        WARNINGMSG("Nothing to print. Charge map is empty");
        return;
    }

    for (auto const &[dt, PICs] : m_chargeDensityMap)
    {
        std::cout << std::format("\033[1;34mTime {} s\n\033[0m", dt);
        for (auto const &[tetrId, charge] : PICs)
            std::cout << std::format("Tetrahedron[{}]: {} C/m³\n", tetrId, charge);
    }
}

std::map<size_t, ParticleVector> ParticleInCellTracker::getParticlesInCell(int time_interval) const
{
    if (m_particlesInCell.empty())
    {
        WARNINGMSG("Data storage for the particles in cell is empty. Returning empty PIC map");
        return std::map<size_t, ParticleVector>();
    }

    if (time_interval < 0)
        throw std::runtime_error("Time interval can't be less than 0, but you specified " + std::to_string(time_interval));

    return m_particlesInCell.at(m_timeMap.at(time_interval));
}

std::map<size_t, double> ParticleInCellTracker::getChargeDensityMap(int time_interval) const
{
    if (m_chargeDensityMap.empty())
    {
        WARNINGMSG("Charge map is empty. Returning empty charge map");
        return std::map<size_t, double>();
    }

    if (time_interval < 0)
        throw std::runtime_error("Time interval can't be less than 0, but you specified " + std::to_string(time_interval));

    return m_chargeDensityMap.at(m_timeMap.at(time_interval));
}
