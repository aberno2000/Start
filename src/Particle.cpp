#ifdef LOG
#include "../include/Settings.hpp"
#include <format>
#endif

#include <utility>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"
#include "../include/Settings.hpp"

void ParticleGeneric::calculateVelocityFromEnergy_J()
{
  // TODO: Here we need to calculate the velocity vector not only for sphere distribution
  // Example below:

  RealNumberGenerator rng;
  [[maybe_unused]] double v{std::sqrt(2 * m_energy / getMass())},
      theta{rng.get_double(0 - std::numeric_limits<long double>::min(),
                           std::numbers::pi + std::numeric_limits<long double>::min())},
      phi{rng.get_double(0 - std::numeric_limits<long double>::min(),
                         2 * std::numbers::pi + std::numeric_limits<long double>::min())},
      vx{m_radius * sin(theta) * cos(phi)},
      vy{m_radius * sin(theta) * sin(phi)},
      vz{m_radius * cos(theta)};

  m_velocity = VelocityVector(vx, vy, vz);
}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_,
                                 double energy_, double radius_)
    : m_cords(MathVector(x_, y_, z_)),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_radius = radius_;
  m_boundingBox = aabb::AABB({x_ - radius_, y_ - radius_, z_ - radius_},
                             {x_ + radius_, y_ + radius_, z_ + radius_});
}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_,
                                 double vx_, double vy_, double vz_,
                                 double radius_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(PositionVector posvec,
                                 double vx_, double vy_, double vz_,
                                 double radius_)
    : m_cords(posvec),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_boundingBox({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                    {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_}) {}

ParticleGeneric::ParticleGeneric(PositionVector posvec, double energy_, double radius_)
    : m_cords(posvec),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_radius = radius_;
  m_boundingBox = aabb::AABB({m_cords.getX() - radius_, m_cords.getY() - radius_, m_cords.getZ() - radius_},
                             {m_cords.getX() + radius_, m_cords.getY() + radius_, m_cords.getZ() + radius_});
}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_,
                                 VelocityVector velvec,
                                 double radius_)
    : m_cords(MathVector(x_, y_, z_)),
      m_velocity(velvec),
      m_radius(radius_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(PositionVector posvec,
                                 VelocityVector velvec,
                                 double radius_)
    : m_cords(posvec),
      m_velocity(velvec),
      m_radius(radius_),
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

bool ParticleGeneric::isOutOfBounds(aabb::AABB const &bounding_volume) const
{
  return (m_boundingBox.lowerBound[0] <= bounding_volume.lowerBound[0] ||
          m_boundingBox.upperBound[0] >= bounding_volume.upperBound[0] ||
          m_boundingBox.lowerBound[1] <= bounding_volume.lowerBound[1] ||
          m_boundingBox.upperBound[1] >= bounding_volume.upperBound[1] ||
          m_boundingBox.lowerBound[2] <= bounding_volume.lowerBound[2] ||
          m_boundingBox.upperBound[2] >= bounding_volume.upperBound[2]);
}

int ParticleGeneric::isParticleInsideTriangle(TriangleMeshParam const &mesh) const
{
  PositionVector v0{std::get<2>(mesh) - std::get<1>(mesh)},
      v1{std::get<3>(mesh) - std::get<1>(mesh)},
      v2{m_cords - std::get<1>(mesh)};

  PositionVector normal{v0.crossProduct(v1)};

  // Check if the point lies on the same plane as the triangle
  // 1e-6 - tolerance value
  if (std::fabs(v2.dotProduct(normal)) > 1e-6)
    return false;

  double dot00{v0.dotProduct(v0)},
      dot01{v0.dotProduct(v1)},
      dot11{v1.dotProduct(v1)},
      dot20{v2.dotProduct(v0)},
      dot21{v2.dotProduct(v1)};

  // Calculating barycentric coordinates
  double denom{dot00 * dot11 - dot01 * dot01},
      u{(dot11 * dot20 - dot01 * dot21) / denom},
      v{(dot00 * dot21 - dot01 * dot20) / denom};

  // Check if point is in triangle
  return ((u >= 0) && (v >= 0) && (u + v <= 1)) ? std::get<0>(mesh) : -1;
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
