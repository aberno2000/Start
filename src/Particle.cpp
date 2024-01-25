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

void ParticleGeneric::calculateEnergyJFromVelocity(double vx, double vy, double vz) { m_energy = getMass() * (VelocityVector(vx, vy, vz).module()) / 2; }
void ParticleGeneric::calculateEnergyJFromVelocity(VelocityVector const &v) { calculateEnergyJFromVelocity(VelocityVector(v.getX(), v.getZ(), v.getZ())); }
void ParticleGeneric::calculateEnergyJFromVelocity(VelocityVector &&v) noexcept { calculateEnergyJFromVelocity(v.getX(), v.getZ(), v.getZ()); }

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
                    {x_ + radius_, y_ + radius_, z_ + radius_})
{
  calculateEnergyJFromVelocity(m_velocity);
}

ParticleGeneric::ParticleGeneric(Point3 centre,
                                 double vx_, double vy_, double vz_,
                                 double radius_)
    : m_centre(centre),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_radius(radius_),
      m_boundingBox({CGAL::to_double(m_centre.x()) - radius_, CGAL::to_double(m_centre.y()) - radius_, CGAL::to_double(m_centre.z()) - radius_},
                    {CGAL::to_double(m_centre.x()) + radius_, CGAL::to_double(m_centre.y()) + radius_, CGAL::to_double(m_centre.z()) + radius_})
{
  calculateEnergyJFromVelocity(m_velocity);
}

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
                    {x_ + radius_, y_ + radius_, z_ + radius_})
{
  calculateEnergyJFromVelocity(m_velocity);
}

ParticleGeneric::ParticleGeneric(Point3 centre,
                                 VelocityVector velvec,
                                 double radius_)
    : m_centre(centre),
      m_velocity(velvec),
      m_radius(radius_),
      m_boundingBox({CGAL::to_double(m_centre.x()) - radius_, CGAL::to_double(m_centre.y()) - radius_, CGAL::to_double(m_centre.z()) - radius_},
                    {CGAL::to_double(m_centre.x()) + radius_, CGAL::to_double(m_centre.y()) + radius_, CGAL::to_double(m_centre.z()) + radius_})
{
  calculateEnergyJFromVelocity(m_velocity);
}

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

double ParticleGeneric::getX() const { return CGAL::to_double(m_centre.x()); }
double ParticleGeneric::getY() const { return CGAL::to_double(m_centre.y()); }
double ParticleGeneric::getZ() const { return CGAL::to_double(m_centre.z()); }
double ParticleGeneric::getPositionModule() const { return PositionVector(CGAL::to_double(m_centre.x()), CGAL::to_double(m_centre.y()), CGAL::to_double(m_centre.z())).module(); }

double ParticleGeneric::getEnergy_eV() const { return m_energy * physical_constants::J_eV; }
double ParticleGeneric::getVelocityModule() const { return m_velocity.module(); }

void ParticleGeneric::colide(double xi, double phi, double p_mass, double t_mass)
{
  RealNumberGenerator rng;
  double xi_cos{rng(-1, 1)}, xi_sin{sqrt(1 - xi_cos * xi_cos)},
      phi{rng(0, 2 * std::numbers::pi)};

  double x{xi_sin * cos(phi)},
      y{xi_sin * sin(phi)},
      z{xi_cos},
      mass_cp{p_mass / (t_mass + p_mass)},
      mass_ct{t_mass / (t_mass + p_mass)};

  VelocityVector cm_vel(m_velocity * mass_cp),
      p_vec(mass_ct * m_velocity);
  double mp{p_vec.module()};
  auto angles{p_vec.calcBetaGamma()};
  VelocityVector dir_vector(x * mp, y * mp, z * mp);
  dir_vector.rotation(angles);

  m_velocity = dir_vector + cm_vel;
}
