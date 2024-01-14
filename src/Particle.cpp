#ifdef LOG
#include <format>
#endif

#include <utility>

#include "../include/Particle.hpp"
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

  // Update the bounding box to the new position
  m_boundingBox = aabb::AABB({m_cords.getX() - m_radius, m_cords.getY() - m_radius, m_cords.getZ() - m_radius},
                             {m_cords.getX() + m_radius, m_cords.getY() + m_radius, m_cords.getZ() + m_radius});
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
  PositionVector A{std::get<1>(mesh).getX(),
                   std::get<1>(mesh).getY(),
                   std::get<1>(mesh).getZ()},
      B{std::get<2>(mesh).getX(),
        std::get<2>(mesh).getY(),
        std::get<2>(mesh).getZ()},
      C{std::get<3>(mesh).getX(),
        std::get<3>(mesh).getY(),
        std::get<3>(mesh).getZ()};

  double areaABC{std::get<4>(mesh)},
      areaPAB{PositionVector::calculateTriangleArea(m_cords, A, B)},
      areaPAC{PositionVector::calculateTriangleArea(m_cords, A, C)},
      areaPBC{PositionVector::calculateTriangleArea(m_cords, B, C)};

  // Check if sum of areas of sub-triangles equals the area of the full triangle
  return (std::fabs(areaPAB + areaPAC + areaPBC - areaABC) < 1e-9)
             ? std::get<0>(mesh)
             : -1;
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
  // Updated velocity = [directory vector ⋅ (mass_ct ⋅ |old velocity|)] + (old velocity ⋅ mass_cp)
  m_velocity = new_vel + cm_vel;
}
