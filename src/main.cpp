#include <future>
#include <mutex>
#include <thread>

#include "../include/DataHandling/HDF5Handler.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Geometry/Mesh.hpp"
#include "../include/Particles/Particles.hpp"

#pragma region CONCURRENT_TRY
void processSegment(ParticleGenericVector &pgs,
                    MeshParamVector const &mesh,
                    double dt, double start_time, double end_time,
                    std::unordered_map<size_t, int> &m)
{
    for (double t{start_time}; t <= end_time; t += dt)
    {
        std::mutex m_mutex;
        for (auto &p : pgs)
        {
            PointD prev(p.getCentre());
            p.updatePosition(dt);
            PointD cur(p.getCentre());

            for (auto const &triangle : mesh)
            {
                size_t id{Mesh::isRayIntersectTriangle(RayD(prev, cur), triangle)};
                if (id != -1ul)
                {
                    {
                        std::lock_guard<std::mutex> lk(m_mutex);
                        ++m[id];
                    }
                    break; // Assume, that particle can settle only on one triangle of the mesh
                }
            }
        }
    }
}

std::unordered_map<size_t, int>
trackCollisionsConcurrent(ParticleGenericVector &pgs,
                          MeshParamVector const &mesh,
                          double dt, double total_time)
{
    std::unordered_map<size_t, int> m;

    // Number of concurrent threads supported by the implementation
    size_t num_threads{std::thread::hardware_concurrency()};
    std::vector<std::jthread> thread_pool;

    double seglen{total_time / num_threads};
    for (size_t i{}; i < num_threads; ++i)
    {
        double start_time{i * seglen},
            end_time{start_time + seglen};
        thread_pool.emplace_back(processSegment, std::ref(pgs), std::cref(mesh), dt, start_time, end_time, std::ref(m));
    }

    return m;
}

void simulateMovementConcurrent(VolumeType vtype, size_t particles_count,
                                double meshSize, int meshDim, double dt, double simtime,
                                std::string_view outfile, std::string_view hdf5filename,
                                int argc, char *argv[])
{
    // 1. Generating bounded volume in GMSH
    GMSHVolumeCreator volumeCreator;

    // 2. Choosing the volume type
    switch (vtype)
    {
    case VolumeType::BoxType:
        volumeCreator.createBoxAndMesh(meshSize, meshDim, outfile);
        break;
    case VolumeType::SphereType:
        volumeCreator.createSphereAndMesh(meshSize, meshDim, outfile);
        break;
    case VolumeType::CylinderType:
        volumeCreator.createCylinderAndMesh(meshSize, meshDim, outfile);
        break;
    case VolumeType::ConeType:
        volumeCreator.createConeAndMesh(meshSize, meshDim, outfile);
        break;
    default:
        std::cerr << "There is no such type\n";
        return;
    }

    // 3. Getting mesh parameters from .msh file
    MeshParamVector mesh{volumeCreator.getMeshParams(outfile)};

    // 4. Creating random particles
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count));

    // 5. Simulating movement - tracking collisions of the particles to walls
    auto counterMap{trackCollisionsConcurrent(pgs, mesh, dt, simtime)};

    // 6. Updating particle counters
    for (auto &triangle : mesh)
        if (auto it{counterMap.find(std::get<0>(triangle))}; it != counterMap.cend())
            std::get<3>(triangle) = it->second;

    // 7. Saving mesh with updated counters to HDF5
    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};

    // 8. Running GMSH
    volumeCreator.runGmsh(argc, argv);
}
#pragma endregion CONCURRENT_TRY

std::unordered_map<size_t, int>
trackCollisions(ParticleGenericVector &pgs,
                MeshParamVector const &mesh,
                double dt, double total_time)
{
    std::unordered_map<size_t, int> m;

    for (double t{}; t <= total_time; t += dt)
    {
        for (auto &p : pgs)
        {
            PointD prevCentre(p.getCentre());
            p.updatePosition(dt);
            PointD nextCentre(p.getCentre());

            for (auto const &triangle : mesh)
            {
                size_t id{Mesh::isRayIntersectTriangle(RayD(prevCentre, nextCentre), triangle)};
                if (id)
                {
                    ++m[id];
                    break;
                }
            }
        }
    }
    return m;
}

void simulateMovement(size_t particles_count, double dt, double simtime,
                      std::string_view outfile, std::string_view hdf5filename)
{
    GMSHVolumeCreator volumeCreator;
    MeshParamVector mesh{volumeCreator.getMeshParams(outfile)};
    ParticleGenericVector pgs(createParticlesWithVelocities<ParticleGeneric>(particles_count));

    auto counterMap{trackCollisions(pgs, mesh, dt, simtime)};
    for (auto &triangle : mesh)
        if (auto it{counterMap.find(std::get<0>(triangle))}; it != counterMap.cend())
            std::get<3>(triangle) = it->second;

    HDF5Handler hdf5handler(hdf5filename);
    hdf5handler.saveMeshToHDF5(mesh);
    auto updatedMesh{hdf5handler.readMeshFromHDF5()};
}

int main(int argc, char *argv[])
{
    if (argc != 3)
    {
        std::cerr << "Usage: " << argv[0] << " <particles_count> <msh_filename>\n";
        return EXIT_FAILURE;
    }
    int particles_count{std::stoi(argv[1])};
    std::string mshfilename(argv[2]),
        hdf5filename(mshfilename.substr(0, mshfilename.find(".")) + ".hdf5");

    simulateMovement(particles_count, 0.1, 10.0, mshfilename, hdf5filename);

    return EXIT_SUCCESS;
}
