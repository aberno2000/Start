#ifdef LOG
#include <format>
#endif

#include <utility>

#include "../include/Particles/Particles.hpp"

void ParticleGeneric::calculateVelocityFromEnergy_J()
{
  // TODO: Here we need to calculate the velocity vector not only for sphere distribution
  // Example below:

  RealNumberGenerator rng;
  [[maybe_unused]] double v{std::sqrt(2 * m_energy / getMass())},
      theta{rng(0 - std::numeric_limits<long double>::min(),
                std::numbers::pi + std::numeric_limits<long double>::min())},
      phi{rng(0 - std::numeric_limits<long double>::min(),
              2 * std::numbers::pi + std::numeric_limits<long double>::min())},
      vx{m_radius * sin(theta) * cos(phi)},
      vy{m_radius * sin(theta) * sin(phi)},
      vz{m_radius * cos(theta)};

  m_velocity = VelocityVector(vx, vy, vz);
}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_,
                                 double energy_, double radius_)
    : m_centre(Point3(x_, y_, z_)),
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
    : m_centre(Point3(x_, y_, z_)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(Point3 centre,
                                 double vx_, double vy_, double vz_,
                                 double radius_)
    : m_centre(centre),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_boundingBox({CGAL::to_double(m_centre.x()) - radius_, CGAL::to_double(m_centre.y()) - radius_, CGAL::to_double(m_centre.z()) - radius_},
                    {CGAL::to_double(m_centre.x()) + radius_, CGAL::to_double(m_centre.y()) + radius_, CGAL::to_double(m_centre.z()) + radius_}) {}

ParticleGeneric::ParticleGeneric(Point3 centre, double energy_, double radius_)
    : m_centre(centre),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_radius = radius_;
  m_boundingBox = aabb::AABB({CGAL::to_double(m_centre.x()) - radius_, CGAL::to_double(m_centre.y()) - radius_, CGAL::to_double(m_centre.z()) - radius_},
                             {CGAL::to_double(m_centre.x()) + radius_, CGAL::to_double(m_centre.y()) + radius_, CGAL::to_double(m_centre.z()) + radius_});
}

ParticleGeneric::ParticleGeneric(double x_, double y_, double z_,
                                 VelocityVector velvec,
                                 double radius_)
    : m_centre(Point3(x_, y_, z_)),
      m_velocity(velvec),
      m_radius(radius_),
      m_boundingBox({x_ - radius_, y_ - radius_, z_ - radius_},
                    {x_ + radius_, y_ + radius_, z_ + radius_}) {}

ParticleGeneric::ParticleGeneric(Point3 centre,
                                 VelocityVector velvec,
                                 double radius_)
    : m_centre(centre),
      m_velocity(velvec),
      m_radius(radius_),
      m_boundingBox({CGAL::to_double(m_centre.x()) - radius_, CGAL::to_double(m_centre.y()) - radius_, CGAL::to_double(m_centre.z()) - radius_},
                    {CGAL::to_double(m_centre.x()) + radius_, CGAL::to_double(m_centre.y()) + radius_, CGAL::to_double(m_centre.z()) + radius_}) {}

void ParticleGeneric::updatePosition(double dt)
{
  // Update particle positions: x = x + Vx ⋅ Δt
  double upd_x{CGAL::to_double(m_centre.x()) + getVx() * dt},
      upd_y{CGAL::to_double(m_centre.y()) + getVy() * dt},
      upd_z{CGAL::to_double(m_centre.z()) + getVz() * dt};

  m_centre = Point3(upd_x, upd_y, upd_z);

  // Update the bounding box to the new position
  m_boundingBox = aabb::AABB({CGAL::to_double(m_centre.x()) - m_radius, CGAL::to_double(m_centre.y()) - m_radius, CGAL::to_double(m_centre.z()) - m_radius},
                             {CGAL::to_double(m_centre.x()) + m_radius, CGAL::to_double(m_centre.y()) + m_radius, CGAL::to_double(m_centre.z()) + m_radius});
}

bool ParticleGeneric::overlaps(ParticleGeneric const &other) const
{
  // Distance between particles
  double distance_{PositionVector(CGAL::to_double(m_centre.x()), CGAL::to_double(m_centre.y()), CGAL::to_double(m_centre.z()))
                       .distance(PositionVector(CGAL::to_double(other.m_centre.x()), CGAL::to_double(other.m_centre.y()), CGAL::to_double(other.m_centre.z())))};
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
