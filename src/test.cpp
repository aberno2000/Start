#include "../include/Particles/Particles.hpp"
#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr double k_mesh_size{10};
static constexpr int k_mesh_dims{3};
static constexpr size_t k_particles_count{100};

int main(int argc, char *argv[])
{
    TetrahedronMeshParamVector tetrahedronMesh;
    GMSHVolumeCreator vc;
    size_t idx{};
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al)};
    for (auto const &particle : particles)
        std::cout << std::format("Particle[{}]: {} {} {}\n",
                                 idx++, particle.getX(), particle.getY(), particle.getZ());
    SphereVector sv;
    for (auto const &particle : particles)
        sv.emplace_back(particle.getCentre(), 1);
    vc.createSpheresAndMesh(sv, 1, 2, k_mesh_filename);

    vc.createBoxAndMesh(k_mesh_size, k_mesh_dims, k_mesh_filename);

    idx = 0;
    for (auto const &tetrahedron : vc.getTetrahedronMeshParams(k_mesh_filename))
        std::cout << std::format("Tetrahedron[{}]:\nVertex A: ({}; {}; {})\nVertex B: ({}; {}; {})\nVertex C: ({}; {}; {})\nVertex D: ({}; {}; {})\nVolume: {}\n",
                                 idx++, CGAL_TO_DOUBLE(tetrahedron.vertex(0).x()), CGAL_TO_DOUBLE(tetrahedron.vertex(0).y()), CGAL_TO_DOUBLE(tetrahedron.vertex(0).z()),
                                 CGAL_TO_DOUBLE(tetrahedron.vertex(1).x()), CGAL_TO_DOUBLE(tetrahedron.vertex(1).y()), CGAL_TO_DOUBLE(tetrahedron.vertex(1).z()),
                                 CGAL_TO_DOUBLE(tetrahedron.vertex(2).x()), CGAL_TO_DOUBLE(tetrahedron.vertex(2).y()), CGAL_TO_DOUBLE(tetrahedron.vertex(2).z()),
                                 CGAL_TO_DOUBLE(tetrahedron.vertex(3).x()), CGAL_TO_DOUBLE(tetrahedron.vertex(3).y()), CGAL_TO_DOUBLE(tetrahedron.vertex(3).z()),
                                 util::calculateVolumeOfTetrahedron3(tetrahedron));
    std::cout << std::format("Total volume is {}\n", Mesh::getVolumeFromTetrahedronMesh(k_mesh_filename));
    vc.runGmsh(argc, argv);

    return EXIT_SUCCESS;
}
