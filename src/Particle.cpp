#ifdef LOG
#include "../include/Settings.hpp"
#include <format>
#endif

#include <utility>

#include "../include/Particle.hpp"
#include "../include/Settings.hpp"

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_, double vx_, double vy_, double vz_, double radius_,
                                 double minBoundary_, double maxBoundary_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(PositionVector posvec, double vx_, double vy_, double vz_, double radius_,
                                 double minBoundary_, double maxBoundary_)
    : m_cords(posvec),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                    {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_}) {}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_, VelocityVector velvec, double radius_,
                                 double minBoundary_, double maxBoundary_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(velvec),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(PositionVector posvec, VelocityVector velvec,
                                 double radius_, double minBoundary_, double maxBoundary_)
    : m_cords(posvec),
      m_velocity(velvec),
      m_radius(radius_),
      m_minBoundary(minBoundary_), m_maxBoundary(maxBoundary_),
      m_boundingBox({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                    {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_}) {}

void ParticleGeneric::updatePosition(double dt)
{
  // Update particle positions: x = x + Vx ⋅ Δt
  m_cords.setXYZ(getX() + getVx() * dt,
                 getY() + getVy() * dt,
                 getZ() + getVz() * dt);
}

bool ParticleGeneric::overlaps(ParticleGeneric const &other) const
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

bool ParticleGeneric::isOutOfBounds() const
{
  return getX() < m_minBoundary || getX() > m_maxBoundary ||
         getY() < m_minBoundary || getY() > m_maxBoundary ||
         getZ() < m_minBoundary || getZ() > m_maxBoundary;
}

void ParticleGeneric::colide(double xi, double phi, double p_mass, double t_mass)
{
  double x{sin(xi) * cos(phi)},
      y{sin(xi) * sin(phi)},
      z{cos(xi)},
      mass_cp{p_mass / (t_mass + p_mass)},
      mass_ct{t_mass / (t_mass + p_mass)};

  VelocityVector dir_vec(x, y, z),
      cm_vel(m_velocity * mass_cp),
      new_vel(dir_vec * (mass_ct * m_velocity.module()));

  // Updating velocity vector of the current particle after collision
  // Updated velocity = [directory vector ⋅ (mass_ct ⋅ |old velocity|)] + (old velocity * mass_cp)
  m_velocity = new_vel + cm_vel;
}
