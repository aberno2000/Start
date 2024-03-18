#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Geometry/Grid3D.hpp"
#include "../include/Particles/Particles.hpp"

static constexpr std::string_view k_mesh_filename{"test.msh"};
static constexpr size_t k_particles_count{100};

/**
 * @brief Checker for point inside the tetrahedron.
 * @param point `Point_3` from CGAL.
 * @param tetrahedron `Tetrahedron_3` from CGAL.
 * @return `true` if point within the tetrahedron, otherwise `false`.
 */
bool isParticleInsideTetrahedron(Particle const &particle, MeshTetrahedronParam const &meshParam)
{
    CGAL::Oriented_side oriented_side{std::get<1>(meshParam).oriented_side(particle.getCentre())};
    if (oriented_side == CGAL::ON_POSITIVE_SIDE)
        return true;
    else if (oriented_side == CGAL::ON_NEGATIVE_SIDE)
        return false;
    else
        // TODO: Correctly handle case when
        return true;
}

int main([[maybe_unused]] int argc, [[maybe_unused]] char *argv[])
{
    // 1. Creating particles
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al)};

    // 2. Creating box in the GMSH application
    GMSHVolumeCreator vc;
    vc.createBoxAndMesh(10, 3, k_mesh_filename);

    // 3. Filling the tetrahedron mesh
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};
    auto endIt{tetrahedronMesh.cend()};

    // 4. Getting edge size from user
    double edgeSize{};
    std::cout << "Enter mesh size (size of the cube edge): ";
    std::cin >> edgeSize;

    // 5. Creating grid
    Grid3D grid(tetrahedronMesh, edgeSize);

    // 6. Start simulating and track particles in each time moment
    std::map<size_t, ParticleVector> particleTracker; ///< Key - tetrahedron ID; Value - particles within tetrahedrons.
    double dt{0.1}, simtime{0.6};
    for (double t{}; t < simtime; t += dt)
    {
        for (auto &pt : particles)
        {
            pt.updatePosition(dt);
            auto meshParams{grid.getTetrahedronsByGridIndex(grid.getGridIndexByPosition(pt.getCentre()))};
            for (auto const &meshParam : meshParams)
                if (isParticleInsideTetrahedron(pt, meshParam))
                    particleTracker[std::get<0>(meshParam)].emplace_back(pt);
        }

        // 6.1_opt. Printing results
        std::cout << std::format("\033[1;34mTime {}\n\033[0m", t);
        for (auto const &[tetrId, pts] : particleTracker)
        {
            std::cout << std::format("Tetrahedron[{}]: ", tetrId);
            for (auto const &pt : pts)
                std::cout << pt.getId() << ' ';
            std::endl(std::cout);
        }
        particleTracker.clear();
    }

    return EXIT_SUCCESS;
}
