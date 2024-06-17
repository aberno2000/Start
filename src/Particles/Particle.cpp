#include <numbers>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Geometry/CGALTypes.hpp"
#include "../include/Particles/Particle.hpp"

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

void Particle::electroMagneticPush(MathVector const &magneticInduction, MathVector const &electricField, double time_step)
{
	// Checking 1. Time step can't be null.
	if (time_step == 0.0)
	{
		WARNINGMSG(util::stringify("There is no any movement in particle[", m_id, "]: Time step is 0"));
		return;
	}

	// Checking 2. If both of vectors are null - just skip pushing particle with EM.
	if (magneticInduction.isNull() && electricField.isNull())
		return;

	// 1. Calculating acceleration using II-nd Newton's Law:
	MathVector a_L{getCharge() * (electricField + m_velocity.crossProduct(magneticInduction)) / getMass()};

	// 2. Acceleration semistep: V_- = V_old + a_L ⋅ Δt/2.
	MathVector v_minus{m_velocity + a_L * time_step / 2.};

	// 3. Rotation:
	/*
		t = qBΔt/(2m).
		s = 2t/(1 + |t|^2).
		V' = V_- + V_- × t.
		V_+ = V_- + V' × s.
	*/
	MathVector t{getCharge() * magneticInduction * time_step / (2. * getMass())},
		s{2. * t / (1 + t.module() * t.module())},
		v_apostrophe{v_minus + v_minus.crossProduct(t)},
		v_plus{v_minus + v_apostrophe.crossProduct(s)};

	// 4. Final acceleration semistep: v_upd = v_+ + a_L ⋅ Δt/2.
	m_velocity = v_plus + a_L * time_step / 2.;
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

ParticleVector createParticlesFromPointSource(std::vector<point_source_t> const &source)
{
	ParticleVector particles;
	for (auto const &sourceData : source)
	{
		std::array<double, 3> thetaPhi = {sourceData.expansionAngle, sourceData.phi, sourceData.theta};
		ParticleType type{util::getParticleTypeFromStrRepresentation(sourceData.type)};

		for (size_t i{}; i < sourceData.count; ++i)
			particles.emplace_back(type,
								   Point(sourceData.baseCoordinates.at(0), sourceData.baseCoordinates.at(1), sourceData.baseCoordinates.at(2)),
								   sourceData.energy,
								   thetaPhi);
	}
	return particles;
}

ParticleVector createParticlesFromSurfaceSource(std::vector<surface_source_t> const &source)
{
    ParticleVector particles;
    std::random_device rd;
    std::mt19937 gen(rd());

    for (auto const &sourceData : source)
    {
        size_t num_cells{sourceData.baseCoordinates.size()},
            particles_per_cell{sourceData.count / num_cells},
            remainder_particles_count{sourceData.count % num_cells};

        std::vector<std::string> keys;
        for (auto const &item : sourceData.baseCoordinates)
            keys.emplace_back(item.first);

        // Randomly distribute the remainder particles.
        std::shuffle(keys.begin(), keys.end(), gen);
        std::vector<size_t> cell_particle_count(num_cells, particles_per_cell);
        for (size_t i{}; i < remainder_particles_count; ++i)
            cell_particle_count[i]++;

        size_t cell_index{};
        ParticleType type{util::getParticleTypeFromStrRepresentation(sourceData.type)};
        for (auto const &item : sourceData.baseCoordinates)
        {
            auto const &cell_centre_str{item.first};
            auto const &normal{item.second};

            // Parse the cell center coordinates from string to double
            std::istringstream iss(cell_centre_str);
            std::vector<double> cell_centre;
            double coord;
            while (iss >> coord)
            {
                cell_centre.push_back(coord);
                if (iss.peek() == ',')
                    iss.ignore();
            }

            for (size_t i{}; i < cell_particle_count[cell_index]; ++i)
            {
                // Calculate theta and phi based on the normal.
                double theta{std::acos(normal.at(2) / std::sqrt(normal.at(0) * normal.at(0) + normal.at(1) * normal.at(1) + normal.at(2) * normal.at(2)))},
                    phi{std::atan2(normal.at(1), normal.at(0))};

                std::array<double, 3> thetaPhi = {0, phi, theta}; // Assume that there is no expansion with surface source.
                particles.emplace_back(type,
                                       Point(cell_centre.at(0), cell_centre.at(1), cell_centre.at(2)),
                                       sourceData.energy,
                                       thetaPhi);
            }
            ++cell_index;
        }
    }
    return particles;
}

std::ostream &operator<<(std::ostream &os, Particle const &particle)
{
	std::cout << std::format("Particle[{}]:\nCenter: {} {} {}\nRadius: {}\nVelocity components: {} {} {}\nEnergy: {} eV\n\n",
							 particle.getId(), particle.getX(), particle.getY(), particle.getZ(), particle.getRadius(),
							 particle.getVx(), particle.getVy(), particle.getVz(), particle.getEnergy_eV());
	return os;
}
