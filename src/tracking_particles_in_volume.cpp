#include <array>
#include <set>

#include <Intrepid2_CellTools.hpp>
#include <Intrepid2_DefaultCubatureFactory.hpp>
#include <Intrepid2_FunctionSpaceTools.hpp>
#include <Intrepid2_HGRAD_TET_C1_FEM.hpp>
#include <Intrepid_FunctionSpaceTools.hpp>
#include <Kokkos_Core.hpp>
#include <Shards_CellTopology.hpp>
#include <eigen3/Eigen/Sparse>

#include "../include/Generators/VolumeCreator.hpp"
#include "../include/Geometry/Grid3D.hpp"
#include "../include/Particles/Particles.hpp"
#include "../include/Utilities/Utilities.hpp"

using namespace Intrepid2;
using ExecutionSpace = Kokkos::DefaultExecutionSpace;
using DeviceType = Kokkos::Device<ExecutionSpace, Kokkos::HostSpace>; // CPU.
using MemorySpace = Kokkos::HostSpace;

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
        // TODO: Correctly handle case when particle is on boundary of tetrahedron.
        return true;
}

int main([[maybe_unused]] int argc, [[maybe_unused]] char *argv[])
{
#pragma region VolumeParticleTracking
    // 1. Creating particles.
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al)};

    // 2. Creating box in the GMSH application.
    GMSHVolumeCreator vc;
    double meshSize{};
    std::cout << "Enter box mesh size: ";
    std::cin >> meshSize;
    vc.createBoxAndMesh(meshSize, 3, k_mesh_filename);

    // 3. Filling the tetrahedron mesh
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};
    auto endIt{tetrahedronMesh.cend()};

    for (auto const &meshParam : tetrahedronMesh)
        std::cout << meshParam << '\n';

    auto tetrahedronNodes{vc.getTetrahedronNodesMap(k_mesh_filename)};
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
    {
        std::cout << std::format("Tetrahedron[{}]: ", tetrahedronID);
        for (size_t nodeID : nodeIDs)
            std::cout << nodeID << ' ';
        std::endl(std::cout);
    }
    std::set<size_t> allNodeIDs;
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
        allNodeIDs.insert(nodeIDs.begin(), nodeIDs.end());
    size_t totalNodes{allNodeIDs.size()};

    // 4. Getting edge size from user.
    double edgeSize{};
    std::cout << "Enter 2nd mesh size (size of the cube edge): ";
    std::cin >> edgeSize;

    // 5. Creating grid.
    Grid3D grid(tetrahedronMesh, edgeSize);

    // 6. Start simulating and track particles in each time moment.
    std::map<size_t, ParticleVector> particleTracker; ///< Key - tetrahedron ID; Value - particles within tetrahedrons.
    double dt{0.1}, simtime{0.5};
    for (double t{}; t <= simtime; t += dt)
    {
        std::cout << std::format("\033[1;34mTime {}\n\033[0m", t);
        for (auto &pt : particles)
        {
            if (t != 0.0)
                pt.updatePosition(dt);

            auto meshParams{grid.getTetrahedronsByGridIndex(grid.getGridIndexByPosition(pt.getCentre()))};
            for (auto const &meshParam : meshParams)
                if (isParticleInsideTetrahedron(pt, meshParam))
                    particleTracker[std::get<0>(meshParam)].emplace_back(pt);
        }

        // 6.1_opt. Printing results.
        size_t count{};
        for (auto const &[tetrId, pts] : particleTracker)
        {
            count += pts.size();
            std::cout << std::format("Tetrahedron[{}]: ", tetrId);
            for (auto const &pt : pts)
                std::cout << pt.getId() << ' ';
            std::endl(std::cout);
        }
        std::cout << "Count of particles: " << count << '\n';
        particleTracker.clear();
    }
#pragma endregion

    Kokkos::initialize();
    {
        std::vector<std::array<int, 4>> globalNodeIndicesPerElement;
        std::vector<std::vector<Kokkos::DynRankView<double, DeviceType>>> allBasisGradients;
        std::vector<Kokkos::DynRankView<double, DeviceType>> allCubWeights;

        // Mapping from node ID to it's index in the global stiffness matrix.
        std::unordered_map<size_t, size_t> nodeID_to_globMatrixID;
        size_t index{};
        for (size_t nodeId : allNodeIDs)
            nodeID_to_globMatrixID[nodeId] = index++;

        for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
        {
            std::array<int, 4> globalNodeIndices;
            for (int i{}; i < 4; ++i)
                globalNodeIndices[i] = nodeID_to_globMatrixID[nodeIDs[i]];
            globalNodeIndicesPerElement.emplace_back(globalNodeIndices);

            auto meshParam{std::ranges::find_if(tetrahedronMesh, [tetrahedronID](auto const &param)
                                                { return std::get<0>(param) == tetrahedronID; })};
            if (meshParam != endIt)
            {
                auto const &[basisFuncs, cubWeights]{util::computeTetrahedronBasisFunctions(*meshParam)};
                allBasisGradients.emplace_back(basisFuncs);
                allCubWeights.emplace_back(cubWeights);
            }
        }

        // Assemblying global stiffness matrix.
        auto globalStiffnessMatrix{util::assembleGlobalStiffnessMatrix(tetrahedronMesh, allBasisGradients, allCubWeights, totalNodes, globalNodeIndicesPerElement)};
        std::cout << globalStiffnessMatrix;
        size_t rows_cols{static_cast<size_t>(std::sqrt(globalStiffnessMatrix.size()))};
        std::cout << std::format("Size of matrix: {}x{}\n", rows_cols, rows_cols);

        // Initializing vector `b` as a resulting vector.
        Eigen::VectorXd b /* {Eigen::VectorXd::Zero(globalStiffnessMatrix.rows())} */;
        util::fillVectorWithRandomNumbers(b, globalStiffnessMatrix.rows());
        std::cout << "Vector `b` for which a solution is being sought:\n"
                  << b << '\n';

        // Calculating equation `Ax=b`:
        Eigen::BiCGSTAB<Eigen::SparseMatrix<double>> solver;
        solver.compute(globalStiffnessMatrix); // Initializing iterative solver with matrix A.
        if (solver.info() != Eigen::Success)
        {
            ERRMSG("Decomposition failed\n");
            return EXIT_FAILURE;
        }

        auto x{solver.solve(b)}; // Utilizing iterative computation of equation Ax=b.
        if (solver.info() != Eigen::Success)
        {
            ERRMSG("Decomposition failed\n");
            return EXIT_FAILURE;
        }
        std::cout << "Solution x-vector:\n"
                  << x << '\n';
    }
    Kokkos::finalize();

    return EXIT_SUCCESS;
}
