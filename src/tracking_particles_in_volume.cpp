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
    // 1. Creating particles.
    auto particles{createParticlesWithVelocities(k_particles_count, particle_types::Al)};

    // 2. Creating box in the GMSH application.
    GMSHVolumeCreator vc;
    double boxMeshSize{};
    std::cout << "Enter box mesh size: ";
    std::cin >> boxMeshSize;
    vc.createBoxAndMesh(boxMeshSize, 3, k_mesh_filename);

    // 3. Filling the tetrahedron mesh
    auto tetrahedronMesh{vc.getTetrahedronMeshParams(k_mesh_filename)};
    auto endIt{tetrahedronMesh.cend()};

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

    Kokkos::initialize();
    {
        // 1. Defining cell topology as tetrahedron.
        shards::CellTopology const cellType{shards::getCellTopologyData<shards::Tetrahedron<4u>>()};
        unsigned int const spaceDim{cellType.getDimension()};

        size_t const numCells{tetrahedronMesh.size()};        // Count of tetrahedrons.
        unsigned int const numNodes{cellType.getNodeCount()}, // 4 verteces.
            dims{3u};                                         // x, y, z.

        // 2. Filling cell nodes with coords of all tetrahedrons verteces.
        Kokkos::DynRankView<double, DeviceType> cell_nodes("cell_nodes", numCells, numNodes, dims);
        for (size_t cell{}; cell < numCells; ++cell)
        {
            auto const &tetrahedron{std::get<1>(tetrahedronMesh.at(cell))};
            for (auto node{0u}; node < numNodes; ++node)
            {
                cell_nodes(cell, node, 0) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).x());
                cell_nodes(cell, node, 1) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).y());
                cell_nodes(cell, node, 2) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).z());
            }
        }

        // 3. Create a basis for linear functions on a tetrahedron.
        Basis_HGRAD_TET_C1_FEM<DeviceType> basis;
        ordinal_type numFields{basis.getCardinality()};
        Intrepid2::DefaultCubatureFactory cubFactory;
        auto cubature{cubFactory.create<DeviceType>(cellType, basis.getDegree())};
        ordinal_type const numCubPoints{cubature->getNumPoints()};

        // 4. Allocate arrays for basis values and their gradients at cubature points.
        Kokkos::DynRankView<double, DeviceType> cub_points("cub_points", numCubPoints, spaceDim);
        Kokkos::DynRankView<double, DeviceType> cub_weights("cub_weights", numCubPoints);
        Kokkos::DynRankView<double, DeviceType> basis_values("basis_values", numFields, numCubPoints);
        Kokkos::DynRankView<double, DeviceType> basis_grads("basis_grads", numFields, numCubPoints, spaceDim);

        // 5. Get cubature points and weights.
        cubature->getCubature(cub_points, cub_weights);

        // 6. Evaluate basis values and gradients at cubature points.
        basis.getValues(basis_values, cub_points, OPERATOR_VALUE);
        basis.getValues(basis_grads, cub_points, OPERATOR_GRAD);

        // 6.1_opt. Printing intermediate results
        std::cout << "Cubature points and weights:\n";
        for (ordinal_type i{}; i < numCubPoints; ++i)
        {
            std::cout << std::format("Cubature point {}: [", i);
            for (unsigned int d{}; d < spaceDim; ++d)
            {
                std::cout << cub_points(i, d);
                if (d < spaceDim - 1)
                    std::cout << ", ";
            }
            std::cout << std::format("], weight: {}\n", cub_weights(i));
        }
        for (ordinal_type i{}; i < numFields; ++i)
        {
            for (ordinal_type j{}; j < numCubPoints; ++j)
            {
                std::cout << std::format("Basis value at field {}, cubature point: {}\n", i, basis_values(i, j));
                std::cout << std::format("Gradient of basis function {} at cubature point {}: [", i, j);
                for (unsigned int k{}; k < spaceDim; ++k)
                {
                    std::cout << basis_grads(i, j, k);
                    if (k < spaceDim - 1)
                        std::cout << ", ";
                }
                std::cout << "]\n";
            }
        }

        // 7. Assemble global stiffness matrix.
        size_t globalMatrixSize{numCells * numNodes}; // Assume one degree of freedom per node for simplicity.
        Eigen::SparseMatrix<double> globalStiffnessMatrix(globalMatrixSize, globalMatrixSize);

        // Helper structure to build the sparse matrix efficiently.
        std::vector<Eigen::Triplet<double>> tripletList;
        tripletList.reserve(numCells * numNodes * numNodes);

        // 7.1. Calculating local stiffness matrices
        for (size_t cellIdx{}; cellIdx < numCells; ++cellIdx)
        {
            // For each cell evaluated own local stiffness matrix based on ∇(basis funcs) and cubature point.
            Kokkos::DynRankView<double, DeviceType> localStiffness("localStiffness", numFields, numFields);
            for (ordinal_type i{}; i < numFields; ++i)
                for (ordinal_type j{}; j < numFields; ++j)
                    for (ordinal_type qp{}; qp < numCubPoints; ++qp)
                        for (unsigned int d{}; d < spaceDim; ++d)
                            localStiffness(i, j) += basis_grads(i, qp, d) * basis_grads(j, qp, d) * cub_weights(qp);

            // Assemble local stiffness matrix into global matrix using triplets.
            for (ordinal_type i{}; i < numFields; ++i)
            {
                for (ordinal_type j{}; j < numFields; ++j)
                {
                    // Convert local node indices to global indices and add to triplet list.
                    size_t globalI{cellIdx * numNodes + i},
                        globalJ{cellIdx * numNodes + j};
                    tripletList.push_back(Eigen::Triplet<double>(globalI, globalJ, localStiffness(i, j)));
                }
            }
        }

        // 7.2. Build sparse matrix from triplets.
        globalStiffnessMatrix.setFromTriplets(tripletList.cbegin(), tripletList.cend());

        // 7_opt. Printing stiffness matrix
        std::cout << "Global stiffness matrix (non-zero entries):\n";
        for (int k = 0; k < globalStiffnessMatrix.outerSize(); ++k)
            for (Eigen::SparseMatrix<double>::InnerIterator it(globalStiffnessMatrix, k); it; ++it)
                std::cout << std::format("({}, {}) = {}\n", it.row(), it.col(), it.value());

        // 8. Calculating equation Ax=b, where b = 0.
        Eigen::SparseMatrix<double> A{globalStiffnessMatrix};
        Eigen::VectorXd b(globalMatrixSize), x(globalMatrixSize);
        b.setZero();

        std::cout << "A matrix:\n"
                  << A << '\n';

        Eigen::BiCGSTAB<Eigen::SparseMatrix<double>> solver;
        solver.compute(A);   // Initializing iterative solver with matrix A.
        x = solver.solve(x); // Utilizing iterative computation of equation Ax=b.

        std::cout << "Solution x:\n";
        if (x.isZero())
            std::cout << "x is vector with all nulls and size " << x.size();
        else
            std::cout << x;
        std::endl(std::cout);

        Eigen::VectorXd r{A * x};       // Since b is already zero -> A*x.
        double residual_norm{r.norm()}; // Compute the Euclidean norm of the residual.
        std::cout << std::format("Residual norm: {}\n", residual_norm);
        std::cout << "Solver information after computation: " << solver.info() << '\n';
    }
    Kokkos::finalize();

    return EXIT_SUCCESS;
}
