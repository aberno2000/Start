#include <cassert>
#include <cmath>
#include <format>
#include <iostream>
#include <sstream>

#include "../include/MathVector.hpp"

void testDefaultConstructor()
{
    MathVector vec;
    assert(vec.getX() == 0.0 && vec.getY() == 0.0 && vec.getZ() == 0.0);
}

void testParameterizedConstructor()
{
    MathVector vec(1.0, 2.0, 3.0);
    assert(vec.getX() == 1.0 && vec.getY() == 2.0 && vec.getZ() == 3.0);
}

void testAssignmentOperator()
{
    MathVector vec;
    vec = 5.0;
    assert(vec.getX() == 5.0 && vec.getY() == 5.0 && vec.getZ() == 5.0);
}

void testCreateCoordinates()
{
    MathVector vec{MathVector::createCoordinates(2.0, 4.0, 6.0)};
    assert(vec.getX() == 2.0 && vec.getY() == 4.0 && vec.getZ() == 6.0);
}

void testModule()
{
    MathVector vec(3.0, 4.0, 12.0);
    assert(fabs(vec.module() - 13.0) < 0.0001);
}

void testDistance()
{
    MathVector vec1(1.0, 2.0, 3.0),
        vec2(4.0, 5.0, 6.0);
    assert(fabs(vec1.distance(vec2) - 5.19615) < 0.0001);
}

void testClear()
{
    MathVector vec(2.0, 3.0, 4.0);
    vec.clear();
    assert(vec.isNull());
}

void testIsNull()
{
    MathVector vec1;
    assert(vec1.isNull());

    MathVector vec2(1.0, 0.0, 0.0);
    assert(!vec2.isNull());

    MathVector vec3(0.0, 0.0, 0.0);
    assert(vec3.isNull());
}

void testIsParallel()
{
    MathVector vec1(1.0, 2.0, 3.0);
    MathVector vec2(2.0, 4.0, 6.0);
    assert(vec1.isParallel(vec2));

    MathVector vec3(1.0, 2.0, 3.0);
    MathVector vec4(-2.0, -4.0, -6.0);
    assert(vec3.isParallel(vec4));

    MathVector vec5(1.0, 2.0, 3.0);
    MathVector vec6(1.0, 2.0, 4.0);
    assert(!vec5.isParallel(vec6));
}

void testIsOrthogonal()
{
    MathVector vec1(1.0, 0.0, 0.0);
    MathVector vec2(0.0, 1.0, 0.0);
    assert(vec1.isOrthogonal(vec2));

    MathVector vec3(1.0, 0.0, 0.0);
    MathVector vec4(1.0, 1.0, 1.0);
    assert(!vec3.isOrthogonal(vec4));
}

void testUnaryMinusOperator()
{
    MathVector vec(1.0, 2.0, 3.0);
    MathVector negatedVec{-vec};
    assert(negatedVec.getX() == -1.0 && negatedVec.getY() == -2.0 && negatedVec.getZ() == -3.0);
}

void testSubtractionOperator()
{
    MathVector vec1(4.0, 5.0, 6.0);
    MathVector vec2(1.0, 2.0, 3.0);
    MathVector result{vec1 - vec2};

    assert(result.getX() == 3.0 && result.getY() == 3.0 && result.getZ() == 3.0);
}

void testAdditionOperator()
{
    MathVector vec1(4.0, 5.0, 6.0);
    MathVector vec2(1.0, 2.0, 3.0);
    MathVector result{vec1 + vec2};

    assert(result.getX() == 5.0 && result.getY() == 7.0 && result.getZ() == 9.0);
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

    // Testing spaceship operator<=>
    assert((vec1 <=> vec2) == std::strong_ordering::equal);
    assert((vec1 <=> vec3) == std::strong_ordering::greater);
    assert((vec3 <=> vec2) == std::strong_ordering::less);

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
    MathVector vec;
    std::istringstream iss("5 6 7");
    iss >> vec;
    MathVector expectedVec(5.0, 6.0, 7.0);

    assert(vec == expectedVec);
}

void testRandomOperations(int test_count = 1'000'000)
{
    for (int i{}; i < test_count; ++i)
    {
        MathVector vec1{MathVector::createRandomVector()},
            vec2{MathVector::createRandomVector()};

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

int main()
{
    testDefaultConstructor();
    testParameterizedConstructor();
    testAssignmentOperator();
    testCreateCoordinates();
    testModule();
    testDistance();
    testClear();
    testIsNull();
    testIsParallel();
    testIsOrthogonal();
    testUnaryMinusOperator();
    testSubtractionOperator();
    testAdditionOperator();
    testSubtractionOperatorWithValue();
    testAdditionOperatorWithValue();
    testFriendAdditionOperatorWithValue();
    testScalarMultiplication();
    testFriendScalarMultiplication();
    testDotProduct();
    testCrossProduct();
    testDivisionOperator();
    testDivisionByZero();
    testComparisonsOperator();
    testOutputStreamOperator();
    testInputStreamOperator();

    std::cout << "1 stage: \033[32;1mAll static tests passed successfully!\033[0m\n";

    int test_count{1'000'000};
    testRandomOperations(test_count);
    std::cout << std::format("2 stage: \033[32;1mAll {} random tests passed successfully!\033[0m\n",
                             test_count);

    return EXIT_SUCCESS;
}
