#include <gtest/gtest.h>

#include "../include/Geometry/MathVector.hpp"

class MathVectorTest : public ::testing::Test
{
};

TEST_F(MathVectorTest, DefaultConstructor)
{
    PositionVector vec;
    EXPECT_DOUBLE_EQ(vec.getX(), 0.0);
    EXPECT_DOUBLE_EQ(vec.getY(), 0.0);
    EXPECT_DOUBLE_EQ(vec.getZ(), 0.0);
}

TEST_F(MathVectorTest, ParameterizedConstructor)
{
    PositionVector vec(1.0, 2.0, 3.0);
    EXPECT_DOUBLE_EQ(vec.getX(), 1.0);
    EXPECT_DOUBLE_EQ(vec.getY(), 2.0);
    EXPECT_DOUBLE_EQ(vec.getZ(), 3.0);
}

TEST_F(MathVectorTest, AssignmentOperator)
{
    PositionVector vec;
    vec = 5.0;
    EXPECT_DOUBLE_EQ(vec.getX(), 5.0);
    EXPECT_DOUBLE_EQ(vec.getY(), 5.0);
    EXPECT_DOUBLE_EQ(vec.getZ(), 5.0);
}

TEST_F(MathVectorTest, CreateCoordinates)
{
    PositionVector vec = PositionVector::createCoordinates(2.0, 4.0, 6.0);
    EXPECT_DOUBLE_EQ(vec.getX(), 2.0);
    EXPECT_DOUBLE_EQ(vec.getY(), 4.0);
    EXPECT_DOUBLE_EQ(vec.getZ(), 6.0);
}

TEST_F(MathVectorTest, Module)
{
    MathVector vec(3.0, 4.0, 12.0);
    EXPECT_NEAR(vec.module(), 13.0, 0.0001);
}

TEST_F(MathVectorTest, Distance)
{
    MathVector vec1(1.0, 2.0, 3.0);
    MathVector vec2(4.0, 5.0, 6.0);
    EXPECT_NEAR(vec1.distance(vec2), 5.19615, 0.0001);
}

TEST_F(MathVectorTest, Clear)
{
    MathVector vec(2.0, 3.0, 4.0);
    vec.clear();
    EXPECT_TRUE(vec.isNull());
}

TEST_F(MathVectorTest, IsNull)
{
    PositionVector vec1;
    EXPECT_TRUE(vec1.isNull());

    MathVector vec2(1.0, 0.0, 0.0);
    EXPECT_FALSE(vec2.isNull());

    MathVector vec3(0.0, 0.0, 0.0);
    EXPECT_TRUE(vec3.isNull());
}

TEST_F(MathVectorTest, IsParallel)
{
    MathVector vec1(1.0, 2.0, 3.0);
    MathVector vec2(2.0, 4.0, 6.0);
    EXPECT_TRUE(vec1.isParallel(vec2));

    MathVector vec3(1.0, 2.0, 3.0);
    MathVector vec4(-2.0, -4.0, -6.0);
    EXPECT_TRUE(vec3.isParallel(vec4));

    MathVector vec5(1.0, 2.0, 3.0);
    MathVector vec6(1.0, 2.0, 4.0);
    EXPECT_FALSE(vec5.isParallel(vec6));
}

TEST_F(MathVectorTest, IsOrthogonal)
{
    MathVector vec1(1.0, 0.0, 0.0);
    MathVector vec2(0.0, 1.0, 0.0);
    EXPECT_TRUE(vec1.isOrthogonal(vec2));

    MathVector vec3(1.0, 0.0, 0.0);
    MathVector vec4(1.0, 1.0, 1.0);
    EXPECT_FALSE(vec3.isOrthogonal(vec4));
}

TEST_F(MathVectorTest, UnaryMinusOperator)
{
    MathVector vec(1.0, 2.0, 3.0);
    MathVector negatedVec = -vec;
    EXPECT_DOUBLE_EQ(negatedVec.getX(), -1.0);
    EXPECT_DOUBLE_EQ(negatedVec.getY(), -2.0);
    EXPECT_DOUBLE_EQ(negatedVec.getZ(), -3.0);
}

TEST_F(MathVectorTest, SubtractionOperator)
{
    MathVector vec1(4.0, 5.0, 6.0);
    MathVector vec2(1.0, 2.0, 3.0);
    MathVector result = vec1 - vec2;
    EXPECT_DOUBLE_EQ(result.getX(), 3.0);
    EXPECT_DOUBLE_EQ(result.getY(), 3.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 3.0);
}

TEST_F(MathVectorTest, AdditionOperator)
{
    MathVector vec1(4.0, 5.0, 6.0);
    MathVector vec2(1.0, 2.0, 3.0);
    MathVector result = vec1 + vec2;
    EXPECT_DOUBLE_EQ(result.getX(), 5.0);
    EXPECT_DOUBLE_EQ(result.getY(), 7.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 9.0);
}

void testSubtractionOperatorWithValue()
{
    MathVector vec(4.0, 5.0, 6.0);
    double value{2.0};
    MathVector resultSubtraction{vec - value};

    assert(resultSubtraction.getX() == 2.0 && resultSubtraction.getY() == 3.0 && resultSubtraction.getZ() == 4.0);
}

void testAdditionOperatorWithValue()
{
    MathVector vec(4.0, 5.0, 6.0);
    double value{2.0};
    MathVector resultAddition{vec + value};

    assert(resultAddition.getX() == 6.0 && resultAddition.getY() == 7.0 && resultAddition.getZ() == 8.0);
}

void testFriendAdditionOperatorWithValue()
{
    MathVector vec(4.0, 5.0, 6.0);
    double value{2.0};
    MathVector resultFriendAddition{value + vec};

    assert(resultFriendAddition.getX() == 6.0 && resultFriendAddition.getY() == 7.0 && resultFriendAddition.getZ() == 8.0);
}

void testScalarMultiplication()
{
    MathVector vec(2.0, 3.0, 4.0);
    double scalar{2.0};
    MathVector resultScalarMult{vec * scalar};

    assert(resultScalarMult.getX() == 4.0 && resultScalarMult.getY() == 6.0 && resultScalarMult.getZ() == 8.0);
}

void testFriendScalarMultiplication()
{
    MathVector vec(2.0, 3.0, 4.0);
    double scalar = 2.0;
    MathVector resultFriendScalarMult = scalar * vec;

    assert(resultFriendScalarMult.getX() == 4.0 && resultFriendScalarMult.getY() == 6.0 && resultFriendScalarMult.getZ() == 8.0);
}

void testDotProduct()
{
    MathVector vec1(2.0, 3.0, 4.0),
        vec2(3.0, 4.0, 5.0);
    double dotProdResult{vec1 * vec2},
        expectedDotProduct{2.0 * 3.0 + 3.0 * 4.0 + 4.0 * 5.0},
        tolerance = 1e-10;

    assert(std::abs(dotProdResult - expectedDotProduct) < tolerance);
}

void testCrossProduct()
{
    MathVector vec1(2.0, 3.0, 4.0);
    MathVector vec2(3.0, 4.0, 5.0);
    MathVector crossProdResult{vec1.crossProduct(vec2)};

    MathVector expectedCrossProduct(
        vec1.getY() * vec2.getZ() - vec1.getZ() * vec2.getY(),
        vec1.getZ() * vec2.getX() - vec1.getX() * vec2.getZ(),
        vec1.getX() * vec2.getY() - vec1.getY() * vec2.getX());

    assert(crossProdResult == expectedCrossProduct);
}

void testDivisionOperator()
{
    MathVector vec(6.0, 8.0, 10.0);
    double divisor{2.0};
    MathVector resultDivision{vec / divisor};

    assert(resultDivision.getX() == 3.0 && resultDivision.getY() == 4.0 && resultDivision.getZ() == 5.0);
}

void testDivisionByZero()
{
    MathVector vec(6.0, 8.0, 10.0);
    double divisor{0.0};

    try
    {
        MathVector resultDivisionByZero{vec / divisor};
    }
    catch (std::overflow_error const &e)
    {
        assert(true);
    }
    catch (...)
    {
        assert(false);
    }
}

void testComparisonsOperator()
{
    MathVector vec1(2.0, 3.0, 4.0);
    MathVector vec2(2.0, 3.0, 4.0);
    MathVector vec3(1.0, 3.0, 4.0);

    // Testing operator==
    assert(vec1 == vec2);
    assert(!(vec1 == vec3));

    // Testing operator!=
    assert(vec1 != vec3);
    assert(!(vec1 != vec2));
}

void testOutputStreamOperator()
{
    MathVector vec(2.0, 3.0, 4.0);
    std::ostringstream oss;
    oss << vec;
    std::string output{oss.str()},
        expectedOutput{"2 3 4"};

    assert(output == expectedOutput);
}

void testInputStreamOperator()
{
    PositionVector vec;
    std::istringstream iss("5 6 7");
    iss >> vec;
    MathVector expectedVec(5.0, 6.0, 7.0);

    assert(vec == expectedVec);
}

void testRandomOperations(int test_count = 1'000'000)
{
    for (int i{}; i < test_count; ++i)
    {
        PositionVector vec1{PositionVector::createRandomVector(1000, -1000)},
            vec2{PositionVector::createRandomVector(-1000, 500)};

        MathVector additionResult{vec1 + vec2},
            subtractionResult{vec1 - vec2};
        double dotProductResult{vec1 * vec2};
        MathVector crossProductResult{vec1.crossProduct(vec2)};
        double moduleResultVec1{std::sqrt(vec1.getX() * vec1.getX() +
                                          vec1.getY() * vec1.getY() +
                                          vec1.getZ() * vec1.getZ())},
            moduleResultVec2{std::sqrt(vec2.getX() * vec2.getX() +
                                       vec2.getY() * vec2.getY() +
                                       vec2.getZ() * vec2.getZ())};

        assert(additionResult == vec2 + vec1);
        assert(subtractionResult == vec1 - vec2);
        assert(dotProductResult == vec1.dotProduct(vec2));
        assert((dotProductResult == 0) ? vec1.isOrthogonal(vec2) : true);
        assert(!vec1.isParallel(vec2) && !vec1.isOrthogonal(vec2));
        assert(moduleResultVec1 == vec1.module() && moduleResultVec2 == vec2.module());
    }
}

TEST_F(MathVectorTest, SubtractionOperatorWithValue)
{
    MathVector vec(4.0, 5.0, 6.0);
    double value = 2.0;
    MathVector result = vec - value;
    EXPECT_DOUBLE_EQ(result.getX(), 2.0);
    EXPECT_DOUBLE_EQ(result.getY(), 3.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 4.0);
}

TEST_F(MathVectorTest, AdditionOperatorWithValue)
{
    MathVector vec(4.0, 5.0, 6.0);
    double value = 2.0;
    MathVector result = vec + value;
    EXPECT_DOUBLE_EQ(result.getX(), 6.0);
    EXPECT_DOUBLE_EQ(result.getY(), 7.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 8.0);
}

TEST_F(MathVectorTest, FriendAdditionOperatorWithValue)
{
    MathVector vec(4.0, 5.0, 6.0);
    double value = 2.0;
    MathVector result = value + vec;
    EXPECT_DOUBLE_EQ(result.getX(), 6.0);
    EXPECT_DOUBLE_EQ(result.getY(), 7.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 8.0);
}

TEST_F(MathVectorTest, ScalarMultiplication)
{
    MathVector vec(2.0, 3.0, 4.0);
    double scalar = 2.0;
    MathVector result = vec * scalar;
    EXPECT_DOUBLE_EQ(result.getX(), 4.0);
    EXPECT_DOUBLE_EQ(result.getY(), 6.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 8.0);
}

TEST_F(MathVectorTest, FriendScalarMultiplication)
{
    MathVector vec(2.0, 3.0, 4.0);
    double scalar = 2.0;
    MathVector result = scalar * vec;
    EXPECT_DOUBLE_EQ(result.getX(), 4.0);
    EXPECT_DOUBLE_EQ(result.getY(), 6.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 8.0);
}

TEST_F(MathVectorTest, DotProduct)
{
    MathVector vec1(2.0, 3.0, 4.0);
    MathVector vec2(3.0, 4.0, 5.0);
    double result = vec1 * vec2;
    EXPECT_DOUBLE_EQ(result, 2 * 3 + 3 * 4 + 4 * 5);
}

TEST_F(MathVectorTest, CrossProduct)
{
    MathVector vec1(1.0, 2.0, 3.0);
    MathVector vec2(4.0, 5.0, 6.0);
    MathVector result = vec1.crossProduct(vec2);
    EXPECT_DOUBLE_EQ(result.getX(), (2.0 * 6.0 - 3.0 * 5.0));
    EXPECT_DOUBLE_EQ(result.getY(), (3.0 * 4.0 - 1.0 * 6.0));
    EXPECT_DOUBLE_EQ(result.getZ(), (1.0 * 5.0 - 2.0 * 4.0));
}

TEST_F(MathVectorTest, DivisionOperator)
{
    MathVector vec(6.0, 8.0, 10.0);
    double divisor = 2.0;
    MathVector result = vec / divisor;
    EXPECT_DOUBLE_EQ(result.getX(), 3.0);
    EXPECT_DOUBLE_EQ(result.getY(), 4.0);
    EXPECT_DOUBLE_EQ(result.getZ(), 5.0);
}

TEST_F(MathVectorTest, DivisionByZero)
{
    MathVector vec(6.0, 8.0, 10.0);
    double divisor = 0.0;
    EXPECT_THROW(vec / divisor, std::overflow_error);
}

TEST_F(MathVectorTest, ComparisonsOperator)
{
    MathVector vec1(2.0, 3.0, 4.0);
    MathVector vec2(2.0, 3.0, 4.0);
    MathVector vec3(1.0, 3.0, 4.0);

    EXPECT_TRUE(vec1 == vec2);
    EXPECT_FALSE(vec1 == vec3);
    EXPECT_TRUE(vec1 != vec3);
    EXPECT_FALSE(vec1 != vec2);
}

TEST_F(MathVectorTest, OutputStreamOperator)
{
    MathVector vec(2.0, 3.0, 4.0);
    std::ostringstream oss;
    oss << vec;
    EXPECT_EQ(oss.str(), "2 3 4");
}

TEST_F(MathVectorTest, InputStreamOperator)
{
    MathVector vec;
    std::istringstream iss("5 6 7");
    iss >> vec;
    EXPECT_DOUBLE_EQ(vec.getX(), 5.0);
    EXPECT_DOUBLE_EQ(vec.getY(), 6.0);
    EXPECT_DOUBLE_EQ(vec.getZ(), 7.0);
}
