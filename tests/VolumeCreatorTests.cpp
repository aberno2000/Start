#include <cassert>
#include <format>
#include <fstream>
#include <gmsh.h>
#include <iostream>
#include <string_view>

#include "../include/RealNumberGenerator.hpp"
#include "../include/VolumeCreator.hpp"

SphereVector read_particle_data(std::string_view filename)
{
    std::ifstream ifs(filename.data());
    if (ifs.bad())
        throw std::runtime_error(std::format("Can't open file {}", filename));

    SphereVector particles;
    double x{}, y{}, z{}, Vx{}, Vy{}, Vz{}, radius{};
    while (ifs >> x >> y >> z >> Vx >> Vy >> Vz >> radius)
        particles.emplace_back(std::make_tuple(x, y, z, radius));

    if (!ifs.eof() && ifs.fail())
        throw std::runtime_error(std::format("Error reading data from file {}", filename));
    ifs.close();

    return particles;
}

inline void testBoxCreating() { assert(VolumeCreator::createBox(10, 10, 10, 10, 20, 30) == 1); }
inline void testSphereCreating() { assert(VolumeCreator::createSphere(5, 5, 5, 5) == 2); }
inline void testCylinderCreating() { assert(VolumeCreator::createCylinder(0, 0, 0, 10, 20, 30, 5) == 3); }
inline void testConeCreating() { assert(VolumeCreator::createCone(25, 25, 25, 10, 20, 30, 5, 10) == 4); }

void testSpheresCreating()
{
    SphereVector svec{read_particle_data("results/particles.txt")};
    std::vector<int> sphereTags{VolumeCreator::createSpheres(SphereSpan(svec.begin(), svec.size()))};
    int tag{5};
    for (int tag_to_check : sphereTags)
        assert(tag_to_check == tag++);
}

SphereVector generateRandomSpheres(int count)
{
    SphereVector spheres;
    RealNumberGenerator rng;

    for (int i{}; i < count; ++i)
        spheres.emplace_back(std::make_tuple(rng.get_double(-100.0, 100.0),
                                             rng.get_double(-100.0, 100.0),
                                             rng.get_double(-100.0, 100.0),
                                             rng.get_double(0, 100.0)));

    return spheres;
}

void testsRandom(int test_count)
{
    for (int i{}; i < test_count; ++i)
    {
        SphereVector spheres{generateRandomSpheres(10)};
        std::vector<int> tags{VolumeCreator::createSpheres(SphereSpan(spheres.data(), spheres.size()))};

        for (int tag : tags)
            assert(tag >= 0);
    }
}

int main()
{
    gmsh::initialize();

    testBoxCreating();
    testSphereCreating();
    testCylinderCreating();
    testConeCreating();
    testSpheresCreating();

    std::cout << "1 stage: \033[32;1mAll static tests passed successfully!\033[0m\n";

    int test_count{1'000};
    testsRandom(test_count);
    std::cout << std::format("2 stage: \033[32;1mAll {} random tests passed successfully!\033[0m\n",
                             test_count);

    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(2);

    gmsh::fltk::run();
    gmsh::finalize();

    return EXIT_SUCCESS;
}
