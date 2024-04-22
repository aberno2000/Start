#include <gtest/gtest.h>

#include "../include/Particles/Particles.hpp"

TEST(ParticleTest, ConstructorAndGetters)
{
    Particle particle(ParticleType::Ar, 1.0, 2.0, 3.0, 1.5e-21);
    EXPECT_EQ(particle.getX(), 1.0);
    EXPECT_EQ(particle.getY(), 2.0);
    EXPECT_EQ(particle.getZ(), 3.0);
    EXPECT_DOUBLE_EQ(particle.getEnergy_J(), 1.5e-21);
}

TEST(ParticleTest, UpdatePosition) {
    Particle particle(ParticleType::Ar, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0);
    particle.updatePosition(1.0);
    EXPECT_EQ(particle.getX(), 100.0);
    EXPECT_EQ(particle.getY(), 100.0);
    EXPECT_EQ(particle.getZ(), 100.0);
}

TEST(ParticleTest, Overlaps) {
    Particle particle1(ParticleType::Ar, 0.0, 0.0, 0.0, 1e-21);
    Particle particle2(ParticleType::Ar, 0.1, 0.1, 0.1, 1e-21);
    EXPECT_TRUE(particle1.overlaps(particle2));
}
