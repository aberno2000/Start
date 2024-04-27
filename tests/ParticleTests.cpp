#include <gtest/gtest.h>

#include "../include/Particles/Particles.hpp"

static constexpr std::array<double, 3> thetaPhi{1, 1, 1};

// Test default constructor
TEST(ParticleTest, DefaultConstructor)
{
    Particle particle;
    EXPECT_EQ(particle.getBoundingBox(), CGAL::Bbox_3(0, 0, 0, 0, 0, 0));
}

// Test constructor with ParticleType only
TEST(ParticleTest, ConstructorWithParticleType)
{
    Particle particle(ParticleType::Ar);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
}

// Test constructor with ParticleType and position, energy
TEST(ParticleTest, ConstructorWithTypeAndPositionAndEnergy)
{
    Particle particle(ParticleType::Ar, 1.0, 2.0, 3.0, 1.5e-21, thetaPhi);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getEnergy_J(), 1.5e-21);
}

// Test constructor with ParticleType and full position and velocity
TEST(ParticleTest, ConstructorWithTypePositionVelocity)
{
    Particle particle(ParticleType::Ar, 1.0, 2.0, 3.0, 10.0, 20.0, 30.0);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getVx(), 10.0);
    EXPECT_DOUBLE_EQ(particle.getVy(), 20.0);
    EXPECT_DOUBLE_EQ(particle.getVz(), 30.0);
}

// Test constructor with ParticleType, const Point reference and velocity
TEST(ParticleTest, ConstructorWithTypeConstPointRefAndVelocity)
{
    Point center(1.0, 2.0, 3.0);
    Particle particle(ParticleType::Ar, center, 10.0, 20.0, 30.0);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getVx(), 10.0);
    EXPECT_DOUBLE_EQ(particle.getVy(), 20.0);
    EXPECT_DOUBLE_EQ(particle.getVz(), 30.0);
}

// Test constructor with ParticleType, rvalue Point and velocity
TEST(ParticleTest, ConstructorWithTypeRvaluePointAndVelocity)
{
    Particle particle(ParticleType::Ar, Point(1.0, 2.0, 3.0), 10.0, 20.0, 30.0);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getVx(), 10.0);
    EXPECT_DOUBLE_EQ(particle.getVy(), 20.0);
    EXPECT_DOUBLE_EQ(particle.getVz(), 30.0);
}

// Test constructor with ParticleType, const Point reference, and energy
TEST(ParticleTest, ConstructorWithTypeConstPointRefAndEnergy)
{
    Point center(1.0, 2.0, 3.0);
    Particle particle(ParticleType::Ar, center, 1.5e-21, thetaPhi);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getEnergy_J(), 1.5e-21);
}

// Test constructor with ParticleType, rvalue Point, and energy
TEST(ParticleTest, ConstructorWithTypeRvaluePointAndEnergy)
{
    Particle particle(ParticleType::Ar, Point(1.0, 2.0, 3.0), 1.5e-21, thetaPhi);
    EXPECT_EQ(particle.getType(), ParticleType::Ar);
    EXPECT_DOUBLE_EQ(particle.getX(), 1.0);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getEnergy_J(), 1.5e-21);
}

// Test updating position based on velocity and time delta
TEST(ParticleTest, UpdatePosition)
{
    Particle particle(ParticleType::Ar, 0.0, 0.0, 0.0, 1.0, 2.0, 3.0);
    double dt = 1.0; // 1 second time step
    particle.updatePosition(dt);

    EXPECT_DOUBLE_EQ(particle.getX(), 1.0); // X should now be initial X + Vx*dt
    EXPECT_DOUBLE_EQ(particle.getY(), 2.0); // Y should now be initial Y + Vy*dt
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.0); // Z should now be initial Z + Vz*dt
}

// Test particle overlap detection
TEST(ParticleTest, Overlaps)
{
    Particle particle1(ParticleType::Ar, 0.0, 0.0, 0.0, 0, thetaPhi);
    Particle particle2(ParticleType::Ar, 0.0, 0.0 + particle2.getRadius(), 0.0, 0, thetaPhi);
    Particle particle3(ParticleType::Ar, 1.0, 1.0, 1.0, 0, thetaPhi);

    EXPECT_TRUE(particle1.overlaps(particle2));  // Close enough to overlap
    EXPECT_FALSE(particle1.overlaps(particle3)); // Too far, no overlap
}

// Test getters for the coords
TEST(ParticleTest, PositionGetters)
{
    Particle particle(ParticleType::Ar, 1.5, 2.5, 3.5, 0, thetaPhi);

    EXPECT_DOUBLE_EQ(particle.getX(), 1.5);
    EXPECT_DOUBLE_EQ(particle.getY(), 2.5);
    EXPECT_DOUBLE_EQ(particle.getZ(), 3.5);
}

// Test the getter for position module
TEST(ParticleTest, PositionModule)
{
    Particle particle(ParticleType::Ar, 3.0, 4.0, 0.0, 0, thetaPhi); // Using a 3-4-5 triangle for easy verification

    EXPECT_DOUBLE_EQ(particle.getPositionModule(), 5.0); // Hypotenuse of the triangle, should be 5
}

// Test the getter for energy in electron volts
TEST(ParticleTest, EnergyGetters)
{
    Particle particle(ParticleType::Ar, 0, 0, 0, 1.602e-19, thetaPhi);

    EXPECT_DOUBLE_EQ(std::round(particle.getEnergy_eV()), 1.0); // Should return 1 electron volt
}

// Test the getter for velocity module
TEST(ParticleTest, VelocityModule)
{
    Particle particle(ParticleType::Ar, 0.0, 0.0, 0.0, 3.0, 4.0, 0.0); // Using a 3-4-5 triangle for easy verification
    EXPECT_DOUBLE_EQ(particle.getVelocityModule(), 5.0);               // Hypotenuse of the triangle, should be 5
}

TEST(ParticleTest, HardSphereCollision)
{
    Particle projective(ParticleType::Ti, 0, 0, 0, 1.602e-19, thetaPhi), gas(ParticleType::Ar);
    EXPECT_TRUE(projective.colideHS(gas, 1.0e20, 0.01));
    EXPECT_FALSE(projective.colideHS(gas, 1, 1));
}

TEST(ParticleTest, VariableHardSphereCollision)
{
    Particle projective(ParticleType::Ag, 0, 0, 0, 1.602e-19, thetaPhi), gas(ParticleType::Ne);
    EXPECT_TRUE(projective.colideVHS(gas, 1.0e20, gas.getViscosityTemperatureIndex(), 0.01));
    EXPECT_FALSE(projective.colideVHS(gas, 1, gas.getViscosityTemperatureIndex(), 1));
}

TEST(ParticleTest, VariableSoftSphereCollision)
{
    Particle projective(ParticleType::Au, 0, 0, 0, 1.602e-19, thetaPhi), gas(ParticleType::He);
    EXPECT_TRUE(projective.colideVSS(gas, 1.0e20, gas.getViscosityTemperatureIndex(), gas.getVSSDeflectionParameter(), 0.01));
    EXPECT_FALSE(projective.colideVSS(gas, 1, gas.getViscosityTemperatureIndex(), gas.getVSSDeflectionParameter(), 1));
}
