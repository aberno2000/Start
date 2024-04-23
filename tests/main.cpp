#include "gtest/gtest.h"

int main(int argc, char **argv)
{
    ::testing::InitGoogleTest(std::addressof(argc), argv);
    return RUN_ALL_TESTS();
}
