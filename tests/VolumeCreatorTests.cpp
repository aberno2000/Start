#include <format>
#include <fstream>
#include <gmsh.h>
#include <iostream>
#include <sstream>
#include <string_view>

#include "../include/VolumeCreator.hpp"

SphereVector read_particle_data(std::string_view filename)
{
    std::ifstream ifs(filename.data());
    if (ifs.bad())
        throw std::runtime_error(std::format("Can't open file {}", filename));

    // SphereVector particles;
    // double x{}, y{}, z{}, Vx{}, Vy{}, Vz{}, radius{};
    // while (ifs >> x >> y >> z >> Vx >> Vy >> Vz >> radius)
    // {
    //     std::cout << x << '\t' << y << '\t' << z << '\n';
    //     particles.emplace_back(std::make_tuple(x, y, z, radius));
    // }

    std::ostringstream oss;
    oss << ifs.rdbuf();

    if (oss.str().empty())
        throw std::runtime_error(std::format("File {} is empty", filename));

    std::cout << oss.str();

    if (!ifs.eof() && ifs.fail())
        throw std::runtime_error(std::format("Error reading data from file {}", filename));
    ifs.close();

    return {};
}

int main()
{
    gmsh::initialize();

    int boxTag = VolumeCreator::createBox(10, 10, 10, 10, 20, 30);
    std::cout << "Created Box with tag: " << boxTag << std::endl;

    int sphereTag = VolumeCreator::createSphere(5, 5, 5, 5);
    std::cout << "Created Sphere with tag: " << sphereTag << std::endl;

    int cylinderTag = VolumeCreator::createCylinder(0, 0, 0, 10, 20, 30, 5);
    std::cout << "Created Cylinder with tag: " << cylinderTag << std::endl;

    int coneTag = VolumeCreator::createCone(25, 25, 25, 10, 20, 30, 5, 10);
    std::cout << "Created Cone with tag: " << coneTag << std::endl;

    SphereVector svec{read_particle_data("../results/particles.txt")};
    std::vector<int> sphereTags{VolumeCreator::createSpheres(SphereSpan(svec.begin(), svec.size()))};
    for (int tag : sphereTags)
        std::cout << tag << '\t';
    std::endl(std::cout);

    gmsh::model::occ::synchronize();
    gmsh::model::mesh::generate(2);

    gmsh::fltk::run();

    gmsh::finalize();

    return EXIT_SUCCESS;
}
