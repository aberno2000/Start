#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Particles/Particles.hpp"

void Particle::calculateVelocityFromEnergy_J()
{
  // TODO: Here we need to calculate the velocity vector not only for sphere distribution
  // Example below:

  RealNumberGenerator rng;
  [[maybe_unused]] double v{std::sqrt(2 * m_energy / getMass())},
      theta{rng(0 - std::numeric_limits<long double>::min(),
                std::numbers::pi + std::numeric_limits<long double>::min())},
      phi{rng(0 - std::numeric_limits<long double>::min(),
              2 * std::numbers::pi + std::numeric_limits<long double>::min())},
      vx{getRadius() * sin(theta) * cos(phi)},
      vy{getRadius() * sin(theta) * sin(phi)},
      vz{getRadius() * cos(theta)};

  m_velocity = VelocityVector(vx, vy, vz);
}

void Particle::calculateEnergyJFromVelocity(double vx, double vy, double vz) { m_energy = getMass() * (VelocityVector(vx, vy, vz).module()) / 2; }
void Particle::calculateEnergyJFromVelocity(VelocityVector const &v) { calculateEnergyJFromVelocity(VelocityVector(v.getX(), v.getZ(), v.getZ())); }
void Particle::calculateEnergyJFromVelocity(VelocityVector &&v) noexcept { calculateEnergyJFromVelocity(v.getX(), v.getZ(), v.getZ()); }

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
                   double energy_)
    : m_type(type_),
      m_centre(Point3(x_, y_, z_)),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_boundingBox = aabb::AABB({x_ - getRadius(), y_ - getRadius(), z_ - getRadius()},
                             {x_ + getRadius(), y_ + getRadius(), z_ + getRadius()});
}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
                   double vx_, double vy_, double vz_)
    : m_type(type_),
      m_centre(Point3(x_, y_, z_)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_boundingBox({x_ - getRadius(), y_ - getRadius(), z_ - getRadius()},
                    {x_ + getRadius(), y_ + getRadius(), z_ + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, Point3 const &centre,
                   double vx_, double vy_, double vz_)
    : m_type(type_),
      m_centre(centre),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_boundingBox({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                    {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, Point3 &&centre,
                   double vx_, double vy_, double vz_)
    : m_type(type_),
      m_centre(std::move(centre)),
      m_velocity(MathVector(vx_, vy_, vz_)),
      m_boundingBox({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                    {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, Point3 const &centre, double energy_)
    : m_type(type_),
      m_centre(centre),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_boundingBox = aabb::AABB({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                             {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) + getRadius()});
}

Particle::Particle(ParticleType type_, Point3 &&centre, double energy_)
    : m_type(type_),
      m_centre(std::move(centre)),
      m_energy(energy_)
{
  calculateVelocityFromEnergy_J();
  m_boundingBox = aabb::AABB({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                             {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) + getRadius()});
}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
                   VelocityVector const &velvec)
    : m_type(type_),
      m_centre(Point3(x_, y_, z_)),
      m_velocity(velvec),
      m_boundingBox({x_ - getRadius(), y_ - getRadius(), z_ - getRadius()},
                    {x_ + getRadius(), y_ + getRadius(), z_ + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
                   VelocityVector &&velvec)
    : m_type(type_),
      m_centre(Point3(x_, y_, z_)),
      m_velocity(std::move(velvec)),
      m_boundingBox({x_ - getRadius(), y_ - getRadius(), z_ - getRadius()},
                    {x_ + getRadius(), y_ + getRadius(), z_ + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, Point3 const &centre,
                   VelocityVector const &velvec)
    : m_type(type_),
      m_centre(centre),
      m_velocity(velvec),
      m_boundingBox({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                    {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

Particle::Particle(ParticleType type_, Point3 &&centre,
                   VelocityVector &&velvec)
    : m_type(type_),
      m_centre(std::move(centre)),
      m_velocity(std::move(velvec)),
      m_boundingBox({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                    {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                     CGAL_TO_DOUBLE(m_centre.z()) + getRadius()}) { calculateEnergyJFromVelocity(m_velocity); }

void Particle::updatePosition(double dt)
{
  // Update particle positions: x = x + Vx ⋅ Δt
  double upd_x{CGAL_TO_DOUBLE(m_centre.x()) + getVx() * dt},
      upd_y{CGAL_TO_DOUBLE(m_centre.y()) + getVy() * dt},
      upd_z{CGAL_TO_DOUBLE(m_centre.z()) + getVz() * dt};

  m_centre = Point3(upd_x, upd_y, upd_z);

  // Update the bounding box to the new position
  m_boundingBox = aabb::AABB({CGAL_TO_DOUBLE(m_centre.x()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) - getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) - getRadius()},
                             {CGAL_TO_DOUBLE(m_centre.x()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.y()) + getRadius(),
                              CGAL_TO_DOUBLE(m_centre.z()) + getRadius()});
}

bool Particle::overlaps(Particle const &other) const
{
  // Distance between particles
  double distance_{PositionVector(CGAL_TO_DOUBLE(m_centre.x()),
                                  CGAL_TO_DOUBLE(m_centre.y()),
                                  CGAL_TO_DOUBLE(m_centre.z()))
                       .distance(PositionVector(CGAL_TO_DOUBLE(other.m_centre.x()),
                                                CGAL_TO_DOUBLE(other.m_centre.y()),
                                                CGAL_TO_DOUBLE(other.m_centre.z())))};
  return distance_ < (getRadius() + other.getRadius());
}

bool Particle::overlaps(Particle &&other) const
{
  double distance_{PositionVector(CGAL_TO_DOUBLE(m_centre.x()),
                                  CGAL_TO_DOUBLE(m_centre.y()),
                                  CGAL_TO_DOUBLE(m_centre.z()))
                       .distance(PositionVector(CGAL_TO_DOUBLE(other.m_centre.x()),
                                                CGAL_TO_DOUBLE(other.m_centre.y()),
                                                CGAL_TO_DOUBLE(other.m_centre.z())))};
  return distance_ < (getRadius() + other.getRadius());
}

bool Particle::isOutOfBounds(aabb::AABB const &bounding_volume) const
{
  return (m_boundingBox.lowerBound[0] <= bounding_volume.lowerBound[0] ||
          m_boundingBox.upperBound[0] >= bounding_volume.upperBound[0] ||
          m_boundingBox.lowerBound[1] <= bounding_volume.lowerBound[1] ||
          m_boundingBox.upperBound[1] >= bounding_volume.upperBound[1] ||
          m_boundingBox.lowerBound[2] <= bounding_volume.lowerBound[2] ||
          m_boundingBox.upperBound[2] >= bounding_volume.upperBound[2]);
}

bool Particle::isOutOfBounds(aabb::AABB &&bounding_volume) const
{
  return (m_boundingBox.lowerBound[0] <= bounding_volume.lowerBound[0] ||
          m_boundingBox.upperBound[0] >= bounding_volume.upperBound[0] ||
          m_boundingBox.lowerBound[1] <= bounding_volume.lowerBound[1] ||
          m_boundingBox.upperBound[1] >= bounding_volume.upperBound[1] ||
          m_boundingBox.lowerBound[2] <= bounding_volume.lowerBound[2] ||
          m_boundingBox.upperBound[2] >= bounding_volume.upperBound[2]);
}

double Particle::getX() const { return CGAL_TO_DOUBLE(m_centre.x()); }
double Particle::getY() const { return CGAL_TO_DOUBLE(m_centre.y()); }
double Particle::getZ() const { return CGAL_TO_DOUBLE(m_centre.z()); }
double Particle::getPositionModule() const { return PositionVector(CGAL_TO_DOUBLE(m_centre.x()), CGAL_TO_DOUBLE(m_centre.y()), CGAL_TO_DOUBLE(m_centre.z())).module(); }

double Particle::getEnergy_eV() const { return m_energy * physical_constants::J_eV; }
double Particle::getVelocityModule() const { return m_velocity.module(); }

void Particle::colide(double p_mass, double t_mass) &
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

ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
                                             double minx, double miny, double minz,
                                             double maxx, double maxy, double maxz,
                                             double minvx, double minvy, double minvz,
                                             double maxvx, double maxvy, double maxvz)
{
  RealNumberGenerator rng;
  ParticleVector particles;

  for (size_t i{}; i < count; ++i)
  {
    double x{rng(minx, maxx)},
        y{rng(miny, maxy)},
        z{rng(minz, maxz)},
        vx{rng(minvx, maxvx)},
        vy{rng(minvy, maxvy)},
        vz{rng(minvz, maxvz)};

    particles.emplace_back(type, x, y, z, vx, vy, vz);
  }

  return particles;
}

ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
                                         double minx, double miny, double minz,
                                         double maxx, double maxy, double maxz,
                                         double minenergy, double maxenergy)
{
  RealNumberGenerator rng;
  ParticleVector particles;

  for (size_t i{}; i < count; ++i)
  {
    double x{rng(minx, maxx)},
        y{rng(miny, maxy)},
        z{rng(minz, maxz)},
        energy{rng(minenergy, maxenergy)};

    particles.emplace_back(type, x, y, z, energy);
  }

  return particles;
}
