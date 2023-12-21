#ifdef LOG
#include "../include/Settings.hpp"
#include <format>
#endif

#include <utility>

#include "../include/Particle.hpp"

Particle::Particle(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_,
                   double minBoundary_, double maxBoundary_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

Particle::Particle(PositionVector posvec, double vx_, double vy_, double vz_, double radius_,
                   double minBoundary_, double maxBoundary_)
    : m_cords(posvec),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                    {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_}) {}

Particle::Particle(double x_, double y_, double z_, VelocityVector velvec, double radius_,
                   double minBoundary_, double maxBoundary_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(velvec),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

Particle::Particle(PositionVector posvec, VelocityVector velvec,
                   double radius_, double minBoundary_, double maxBoundary_)
    : m_cords(posvec),
      m_velocity(velvec),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                    {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_}) {}

void Particle::updatePosition(double dt)
{
    // TODO: Velocity changing by collision

    m_cords.setX(m_cords.getX() + m_velocity.getX() * dt);
    m_cords.setY(m_cords.getY() + m_velocity.getY() * dt);
    m_cords.setZ(m_cords.getZ() + m_velocity.getZ() * dt);

    // Ensure particles stay within the boundaries
    m_cords.setX(std::min(std::max(m_cords.getX(), m_minBoundary), m_maxBoundary));
    m_cords.setY(std::min(std::max(m_cords.getY(), m_minBoundary), m_maxBoundary));
    m_cords.setZ(std::min(std::max(m_cords.getZ(), m_minBoundary), m_maxBoundary));
}

bool Particle::overlaps(Particle const &other) const
{
    // Distance between particles
    double distance_{m_cords.distance(other.m_cords)};
#ifdef LOG
    if (distance_ < (m_radius + other.m_radius))
        LOGMSG(std::format("\033[1;36m{:.6f} < {:.6f}\033[0m\033[1m",
                           distance_, m_radius + other.m_radius));
#endif
    return distance_ < (m_radius + other.m_radius);
}
