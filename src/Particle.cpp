#include <numbers>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Geometry/CGALTypes.hpp"
#include "../include/Particles/Particles.hpp"

std::atomic<size_t> Particle::m_nextId{0ul};

void Particle::calculateVelocityFromEnergy_J(std::array<double, 3> const &thetaPhi)
{
	auto [thetaUsers, phiCalculated, thetaCalculated]{thetaPhi};
	RealNumberGenerator rng;

	double theta{thetaCalculated + rng(-1, 1) * thetaUsers},
		v{std::sqrt(2 * getEnergy_J() / getMass())},
		vx{v * std::sin(theta) * std::cos(phiCalculated)},
		vy{v * std::sin(theta) * std::sin(phiCalculated)},
		vz{v * std::cos(theta)};

	m_velocity = VelocityVector(vx, vy, vz);
}

void Particle::calculateEnergyJFromVelocity(double vx, double vy, double vz) { m_energy = getMass() * std::pow((VelocityVector(vx, vy, vz).module()), 2) / 2; }
void Particle::calculateEnergyJFromVelocity(VelocityVector const &v) { calculateEnergyJFromVelocity(VelocityVector(v.getX(), v.getZ(), v.getZ())); }
void Particle::calculateEnergyJFromVelocity(VelocityVector &&v) noexcept { calculateEnergyJFromVelocity(v.getX(), v.getZ(), v.getZ()); }

void Particle::calculateBoundingBox()
{
	m_bbox = CGAL::Bbox_3(getX() - getRadius(), getY() - getRadius(), getZ() - getRadius(),
						  getX() + getRadius(), getY() + getRadius(), getZ() + getRadius());
}

Particle::Particle(ParticleType type_)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(Point(0, 0, 0)),
	  m_velocity(0, 0, 0),
	  m_bbox(0, 0, 0, 0, 0, 0) {}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
				   double energyJ_, std::array<double, 3> const &thetaPhi)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(Point(x_, y_, z_)),
	  m_energy(energyJ_)
{
	calculateVelocityFromEnergy_J(thetaPhi);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
				   double vx_, double vy_, double vz_)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(Point(x_, y_, z_)),
	  m_velocity(MathVector(vx_, vy_, vz_))
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point const &centre,
				   double vx_, double vy_, double vz_)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(centre),
	  m_velocity(MathVector(vx_, vy_, vz_))
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point &&centre,
				   double vx_, double vy_, double vz_)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(std::move(centre)),
	  m_velocity(MathVector(vx_, vy_, vz_))
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point const &centre, double energyJ_,
				   std::array<double, 3> const &thetaPhi)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(centre),
	  m_energy(energyJ_)
{
	calculateVelocityFromEnergy_J(thetaPhi);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point &&centre, double energyJ_,
				   std::array<double, 3> const &thetaPhi)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(std::move(centre)),
	  m_energy(energyJ_)
{
	calculateVelocityFromEnergy_J(thetaPhi);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
				   VelocityVector const &velvec)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(Point(x_, y_, z_)),
	  m_velocity(velvec)
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, double x_, double y_, double z_,
				   VelocityVector &&velvec)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(Point(x_, y_, z_)),
	  m_velocity(std::move(velvec))
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point const &centre,
				   VelocityVector const &velvec)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(centre),
	  m_velocity(velvec)
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

Particle::Particle(ParticleType type_, Point &&centre,
				   VelocityVector &&velvec)
	: m_id(m_nextId++),
	  m_type(type_),
	  m_centre(std::move(centre)),
	  m_velocity(std::move(velvec))
{
	calculateEnergyJFromVelocity(m_velocity);
	calculateBoundingBox();
}

void Particle::updatePosition(double dt)
{
	// Update particle positions: x = x + Vx ⋅ Δt
	double upd_x{CGAL_TO_DOUBLE(m_centre.x()) + getVx() * dt},
		upd_y{CGAL_TO_DOUBLE(m_centre.y()) + getVy() * dt},
		upd_z{CGAL_TO_DOUBLE(m_centre.z()) + getVz() * dt};

	m_centre = Point(upd_x, upd_y, upd_z);
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

double Particle::getX() const { return CGAL_TO_DOUBLE(m_centre.x()); }
double Particle::getY() const { return CGAL_TO_DOUBLE(m_centre.y()); }
double Particle::getZ() const { return CGAL_TO_DOUBLE(m_centre.z()); }
double Particle::getPositionModule() const { return PositionVector(CGAL_TO_DOUBLE(m_centre.x()), CGAL_TO_DOUBLE(m_centre.y()), CGAL_TO_DOUBLE(m_centre.z())).module(); }

double Particle::getEnergy_eV() const { return m_energy * physical_constants::J_eV; }
double Particle::getVelocityModule() const { return m_velocity.module(); }

bool Particle::colide(Particle target, double n_concentration, std::string_view model, double time_step)
{
	if (std::string(model) == "HS")
		return colideHS(target, n_concentration, time_step);
	else if (std::string(model) == "VHS")
		return colideVHS(target, n_concentration, target.getViscosityTemperatureIndex(), time_step);
	else if (std::string(model) == "VSS")
		return colideVSS(target, n_concentration, target.getViscosityTemperatureIndex(), target.getVSSDeflectionParameter(), time_step);
	else
		ERRMSG("No such kind of scattering model. Available only: HS/VHS/VSS");
	return false;
}

bool Particle::colideHS(Particle target, double n_concentration, double time_step)
{

	double p_mass{getMass()},
		t_mass{target.getMass()},
		sigma{(std::numbers::pi)*std::pow(getRadius() + target.getRadius(), 2)};

	// Probability of the scattering
	double Probability{sigma * getVelocityModule() * n_concentration * time_step};

	// Result of the collision: if colide -> change attributes of the particle
	RealNumberGenerator rng;
	bool iscolide{rng() < Probability};
	if (iscolide)
	{
		double xi_cos{rng(-1, 1)}, xi_sin{sqrt(1 - xi_cos * xi_cos)},
			phi{rng(0, 2 * std::numbers::pi)};

		double x{xi_sin * cos(phi)}, y{xi_sin * sin(phi)}, z{xi_cos},
			mass_cp{p_mass / (t_mass + p_mass)},
			mass_ct{t_mass / (t_mass + p_mass)};

		VelocityVector cm_vel(m_velocity * mass_cp), p_vec(mass_ct * m_velocity);
		double mp{p_vec.module()};
		VelocityVector dir_vector(x * mp, y * mp, z * mp);

		m_velocity = dir_vector + cm_vel;
	}
	return iscolide;
}

bool Particle::colideVHS(Particle target, double n_concentration, double omega, double time_step)
{

	double d_reference{(getRadius() + target.getRadius())},
		mass_constant{getMass() * target.getMass() / (getMass() + target.getMass())},
		t_mass{target.getMass()}, p_mass{getMass()},
		Exponent{omega - 1. / 2.};

	double d_vhs_2{(std::pow(d_reference, 2) / std::tgamma(5. / 2. - omega)) *
				   std::pow(2 * KT_reference /
								(mass_constant * getVelocityModule() * getVelocityModule()),
							Exponent)};

	double sigma{std::numbers::pi * d_vhs_2},
		Probability{sigma * getVelocityModule() * n_concentration * time_step};

	RealNumberGenerator rng;
	bool iscolide{rng() < Probability};
	if (iscolide)
	{
		double xi_cos{rng(-1, 1)}, xi_sin{sqrt(1 - xi_cos * xi_cos)},
			phi{rng(0, 2 * std::numbers::pi)};

		double x{xi_sin * cos(phi)}, y{xi_sin * sin(phi)}, z{xi_cos},
			mass_cp{p_mass / (t_mass + p_mass)},
			mass_ct{t_mass / (t_mass + p_mass)};

		VelocityVector cm_vel(m_velocity * mass_cp), p_vec(mass_ct * m_velocity);
		double mp{p_vec.module()};
		VelocityVector dir_vector(x * mp, y * mp, z * mp);

		m_velocity = dir_vector + cm_vel;
	}

	return iscolide;
}

bool Particle::colideVSS(Particle target, double n_concentration, double omega,
						 double alpha, double time_step)
{

	double d_reference{(getRadius() + target.getRadius())},
		mass_constant{getMass() * target.getMass() / (getMass() + target.getMass())},
		t_mass{target.getMass()},
		p_mass{getMass()},
		Exponent{omega - 1. / 2.};

	double d_vhs_2{(std::pow(d_reference, 2) / std::tgamma(5. / 2. - omega)) *
				   std::pow(2 * KT_reference /
								(mass_constant * getVelocityModule() * getVelocityModule()),
							Exponent)};

	double sigma{std::numbers::pi * d_vhs_2},
		Probability{sigma * getVelocityModule() * n_concentration * time_step};

	RealNumberGenerator rng;
	bool iscolide{rng() < Probability};
	if (iscolide)
	{
		double xi_cos{2 * std::pow(rng(), 1. / alpha) - 1.}, xi_sin{sqrt(1 - xi_cos * xi_cos)},
			phi{rng(0, 2 * std::numbers::pi)};

		double x{xi_sin * cos(phi)}, y{xi_sin * sin(phi)}, z{xi_cos},
			mass_cp{p_mass / (t_mass + p_mass)},
			mass_ct{t_mass / (t_mass + p_mass)};

		VelocityVector cm_vel(m_velocity * mass_cp), p_vec(mass_ct * m_velocity);
		double mp{p_vec.module()};
		auto angles{p_vec.calcBetaGamma()};
		VelocityVector dir_vector(x * mp, y * mp, z * mp);
		dir_vector.rotation(angles);

		m_velocity = dir_vector + cm_vel;
	}
	return iscolide;
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
		particles.emplace_back(type,
							   rng(minx, maxx), rng(miny, maxy), rng(minz, maxz),
							   rng(minvx, maxvx), rng(minvy, maxvy), rng(minvz, maxvz));
	return particles;
}

ParticleVector createParticlesWithVelocities(size_t count, ParticleType type,
											 double x, double y, double z,
											 double vx, double vy, double vz)
{
	ParticleVector particles;
	for (size_t i{}; i < count; ++i)
		particles.emplace_back(type, x, y, z, vx, vy, vz);
	return particles;
}

ParticleVector createParticlesWithVelocityModule(size_t count, ParticleType type,
												 double x, double y, double z,
												 double v, double theta, double phi)
{
	RealNumberGenerator rng;
	ParticleVector particles;

	for (size_t i{}; i < count; ++i)
	{
		theta = rng(0, theta);
		phi = rng(0, phi);

		double vx{v * sin(theta) * cos(phi)},
			vy{v * sin(theta) * sin(phi)},
			vz{v * cos(theta)};
		particles.emplace_back(type, x, y, z, vx, vy, vz);
	}

	return particles;
}

ParticleVector createParticlesWithEnergy(size_t count, ParticleType type,
										 double energy,
										 std::array<double, 6> const &particleSourceBaseAndDirection)
{
	std::array<double, 3> thetaPhi;
	thetaPhi[0] = particleSourceBaseAndDirection[3];
	thetaPhi[1] = particleSourceBaseAndDirection[4];
	thetaPhi[2] = particleSourceBaseAndDirection[5];

	ParticleVector particles;
	for (size_t i{}; i < count; ++i)
		particles.emplace_back(type,
							   Point(particleSourceBaseAndDirection[0], particleSourceBaseAndDirection[1], particleSourceBaseAndDirection[2]),
							   energy, thetaPhi);
	return particles;
}

std::ostream &operator<<(std::ostream &os, Particle const &particle)
{
	std::cout << std::format("Particle[{}]:\nCenter: {} {} {}\nRadius: {}\nVelocity components: {} {} {}\nEnergy: {} eV\n\n",
							 particle.getId(), particle.getX(), particle.getY(), particle.getZ(), particle.getRadius(),
							 particle.getVx(), particle.getVy(), particle.getVz(), particle.getEnergy_eV());
	return os;
}
