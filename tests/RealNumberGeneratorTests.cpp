#include <gtest/gtest.h>

#include "../include/Generators/RealNumberGenerator.hpp"

class RealNumberGeneratorTest : public ::testing::Test
{
protected:
    RealNumberGenerator rng;
    RealNumberGenerator rng_range{0.0, 1.0};

    // Additional setup can go here if needed
};

TEST_F(RealNumberGeneratorTest, DefaultConstructor) { EXPECT_NO_THROW(RealNumberGenerator rng); }

TEST_F(RealNumberGeneratorTest, RangeConstructor) { EXPECT_NO_THROW(RealNumberGenerator rng(0.0, 1.0)); }

TEST_F(RealNumberGeneratorTest, CallOperatorWithoutParams)
{
    double result{rng_range()};
    EXPECT_GE(result, 0.0);
    EXPECT_LE(result, 1.0);
}

TEST_F(RealNumberGeneratorTest, CallOperatorWithParams)
{
    double result{rng_range(-1.0, 1.0)};
    EXPECT_GE(result, -1.0);
    EXPECT_LE(result, 1.0);
}

TEST_F(RealNumberGeneratorTest, GetDouble)
{
    double result{rng.get_double(2.0, 3.0)};
    EXPECT_GE(result, 2.0);
    EXPECT_LE(result, 3.0);
}

TEST_F(RealNumberGeneratorTest, SetBounds)
{
    rng.set(5.0, 10.0);
    double result{rng()};
    EXPECT_GE(result, 5.0);
    EXPECT_LE(result, 10.0);
}

TEST_F(RealNumberGeneratorTest, SetLowerBound)
{
    rng.set_lower_bound(10.0);
    double result{rng(10.0, 15.0)};
    EXPECT_GE(result, 10.0);
    EXPECT_LE(result, 15.0);
}

TEST_F(RealNumberGeneratorTest, SetUpperBound)
{
    rng.set_upper_bound(20.0);

    double result{rng(15.0, 20.0)};
    EXPECT_GE(result, 15.0);
    EXPECT_LE(result, 20.0);
}

TEST_F(RealNumberGeneratorTest, GetNegativeSequence)
{
    auto seq{rng.get_sequence(5'000'000, -10'000, 0)};
    ASSERT_EQ(seq.size(), 5'000'000);
    for (double num : seq)
    {
        EXPECT_GE(num, -10'000);
        EXPECT_LE(num, 0);
    }
}

TEST_F(RealNumberGeneratorTest, GetPositiveSequence)
{
    auto seq{rng.get_sequence(5'000'000, 0, 10'000)};
    ASSERT_EQ(seq.size(), 5'000'000);
    for (double num : seq)
    {
        EXPECT_GE(num, 0);
        EXPECT_LE(num, 10'000);
    }
}

TEST_F(RealNumberGeneratorTest, GetMixedSequence)
{
    auto seq{rng.get_sequence(5'000'000, -10'000, 10'000)};
    ASSERT_EQ(seq.size(), 5'000'000);
    for (double num : seq)
    {
        EXPECT_GE(num, -10'000);
        EXPECT_LE(num, 10'000);
    }
}

TEST_F(RealNumberGeneratorTest, GetReversedMixedSequence)
{
    auto seq{rng.get_sequence(5'000'000, 10'000, -10'000)};
    ASSERT_EQ(seq.size(), 5'000'000);
    for (double num : seq)
    {
        EXPECT_GE(num, -10'000);
        EXPECT_LE(num, 10'000);
    }
}

