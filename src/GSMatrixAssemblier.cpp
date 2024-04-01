#include <set>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Utilities/GSMatrixAssemblier.hpp"

BasisFuncValues_CubatureWeights GSMatrixAssemblier::computeTetrahedronBasisFunctions(MeshTetrahedronParam const &meshParam) const
{
    // Defining cell topology as tetrahedron.
    shards::CellTopology cellTopology{shards::getCellTopologyData<shards::Tetrahedron<>>()};
    Intrepid2::Basis_HGRAD_TET_C1_FEM<DeviceType> basis;

    // Using cubature factory to create cubature function.
    Intrepid2::DefaultCubatureFactory cubFactory;
    auto cubature{cubFactory.create<DeviceType>(cellTopology.getBaseKey(), basis.getDegree())};

    auto numCubPoints{cubature->getNumPoints()}; // Getting number of cubature points.
    auto spaceDim{cubature->getDimension()};     // Getting dimension (for tetrahedron, obviously - 3D).

    // Allocating memory for cubature poinst and weights.
    DynRankView cubPoints("cubPoints", numCubPoints, spaceDim);
    DynRankView cubWeights("cubWeights", numCubPoints);

    // Allocating memory for values of basis functions.
    auto numFields{basis.getCardinality()};
    DynRankView basisValues("basisValues", numFields, numCubPoints);
    DynRankView transformedBasisValues("transformedBasisValues", 1, numFields, numCubPoints);

    // Getting cubature points and weights.
    cubature->getCubature(cubPoints, cubWeights);

    // Getting tetrahedron coordinates of each vertex.
    DynRankView vertices("vertices", 1, 4, 3);
    auto tetrahedron{std::get<1>(meshParam)};
    for (short node{}; node < 4; ++node)
    {
        vertices(0, node, 0) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).x());
        vertices(0, node, 1) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).y());
        vertices(0, node, 2) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).z());
    }

    // Calculating basis functions on cubature points.
    basis.getValues(basisValues, cubPoints, Intrepid2::OPERATOR_VALUE);
    DynRankViewVector basisFunctionsValues;
    for (LocalOrdinal i{}; i < numFields; ++i)
    {
        DynRankView fieldValues("fieldValues", numCubPoints);
        for (LocalOrdinal j{}; j < numCubPoints; ++j)
            fieldValues(j) = basisValues(i, j);
        basisFunctionsValues.emplace_back(fieldValues);
    }

    // Transforming basis functions from relative values to physical space.
    Intrepid2::CellTools<DeviceType>::mapToPhysicalFrame(transformedBasisValues, cubPoints, vertices, cellTopology);

    // Opt: printing transformed basis values in all cubature points.
    for (LocalOrdinal i{}; i < numFields; ++i)
        for (LocalOrdinal j{}; j < numCubPoints; ++j)
            std::cout << std::format("Tetrahedron[{}]: Transformed basis function {} at cubature point {} = {}\n",
                                     std::get<0>(meshParam), i, j, transformedBasisValues(0, i, j));
    return std::make_pair(basisFunctionsValues, cubWeights);
}

DynRankView GSMatrixAssemblier::computeLocalStiffnessMatrix(DynRankViewVector const &basisGradients, DynRankView const &cubWeights) const
{
    // Getting count of basis functions and count of cubature points.
    auto const numFields{basisGradients.size()};
    auto const numCubPoints{cubWeights.extent(0)};

    DynRankView localStiffnessMatrix("localStiffnessMatrix", numFields, numFields); // Creating local stiffness matrix.
    Kokkos::deep_copy(localStiffnessMatrix, 0.0);                                   // Initialization of local stiffness matrix with nulls.

    // Calculating local stiffness matrix.
    for (size_t i{}; i < numFields; ++i)
        for (size_t j{}; j < numFields; ++j)
            for (size_t qp{}; qp < numCubPoints; ++qp)
                for (short d{}; d < 3; ++d)
                    localStiffnessMatrix(i, j) += basisGradients[i](qp, d) * basisGradients[j](qp, d) * cubWeights(qp);
    return localStiffnessMatrix;
}

EigenSparseMatrix GSMatrixAssemblier::assembleGlobalStiffnessMatrixHelper(
    MeshTetrahedronParamVector const &meshParams,
    DynRankViewMatrix const &allBasisGradients,
    DynRankViewVector const &allCubWeights,
    GlobalOrdinal totalNodes,
    TetrahedronIndecesVector const &globalNodeIndicesPerElement) const
{
    // Initialization of the global stiffness matrix.
    EigenSparseMatrix globalStiffnessMatrix(totalNodes, totalNodes);

    // List for store non-null elements.
    EigenTripletVector tripletList;
    for (size_t elemIndex{}; elemIndex < meshParams.size(); ++elemIndex)
    {
        // Calculating local stiffness matrix.
        auto localStiffnessMatrix{computeLocalStiffnessMatrix(allBasisGradients[elemIndex], allCubWeights[elemIndex])};

        // Indeces of global nodes for the current tetrahedron.
        auto const &globalNodeIndices{globalNodeIndicesPerElement[elemIndex]};

        // Adding local stiffness matrix to the global.
        for (short i{}; i < 4; ++i)
            for (short j{}; j < 4; ++j)
                tripletList.emplace_back(
                    globalNodeIndices[i],
                    globalNodeIndices[j],
                    localStiffnessMatrix(i, j));
    }

    // Assemblying global matrix from the triplets.
    globalStiffnessMatrix.setFromTriplets(tripletList.begin(), tripletList.end());
    return globalStiffnessMatrix;
}

GSMatrixAssemblier::GSMatrixAssemblier(std::string_view mesh_filename)
    : m_meshfilename(mesh_filename), m_comm(Tpetra::getDefaultComm()), m_gsmatrix(assembleGlobalStiffnessMatrix(m_meshfilename)) {}

Teuchos::RCP<TpetraMatrixType> GSMatrixAssemblier::convertEigenToTpetra(EigenSparseMatrix const &eigenMatrix) const
{
    auto const numGlobalEntries{eigenMatrix.rows()};
    TpetraMatrixType tpetraMatrix(m_map, numGlobalEntries);

    // Insert values from Eigen matrix into Tpetra matrix
    for (int k{}; k < eigenMatrix.outerSize(); ++k)
        for (Eigen::SparseMatrix<double>::InnerIterator it(eigenMatrix, k); it; ++it)
            tpetraMatrix.insertGlobalValues(it.row(), Teuchos::tuple<GlobalOrdinal>(it.col()), Teuchos::tuple<Scalar>(it.value()));
    tpetraMatrix.fillComplete(); // Finilize matrix assembly.

    return Teuchos::rcp(new TpetraMatrixType(std::move(tpetraMatrix)));
}

void GSMatrixAssemblier::printDynRankView(DynRankView const &view) const
{
    auto numRows{view.extent(0)};
    auto numCols{view.extent(1)};

    for (size_t i{}; i < numRows; ++i)
    {
        for (size_t j{}; j < numCols; ++j)
            std::cout << view(i, j) << ' ';
        std::cout << std::endl;
    }
}

void GSMatrixAssemblier::print() const
{
    auto myRank{m_comm->getRank()};
    auto numProcs{m_comm->getSize()};

    // Loop over all processes in sequential order.
    m_comm->barrier();
    for (int proc{}; proc < numProcs; ++proc)
    {
        if (myRank == proc)
        {
            // Print the matrix entries for the current process.
            auto rowMap{m_gsmatrix->getRowMap()};
            size_t localNumRows{rowMap->getLocalNumElements()};

            for (size_t i{}; i < localNumRows; ++i)
            {
                GlobalOrdinal globalRow{rowMap->getGlobalElement(i)};
                size_t numEntries{m_gsmatrix->getNumEntriesInGlobalRow(globalRow)};

                TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
                TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);
                size_t checkNumEntries{};

                m_gsmatrix->getGlobalRowCopy(globalRow, indices, values, checkNumEntries);

                // Now print the row's entries.
                std::cout << std::format("Row {}: ", globalRow);
                for (size_t k{}; k < checkNumEntries; ++k)
                    std::cout << std::format("({}, {}) ", indices[k], values[k]);
                std::endl(std::cout);
            }
        }
        // Synchronize all processes.
        m_comm->barrier();
    }
    m_comm->barrier();
}

Teuchos::RCP<TpetraMatrixType> GSMatrixAssemblier::assembleGlobalStiffnessMatrix(std::string_view mesh_filename)
{
    TetrahedronIndecesVector globalNodeIndicesPerElement;
    DynRankViewMatrix allBasisGradients;
    DynRankViewVector allCubWeights;

    auto tetrahedronMesh{Mesh::getTetrahedronMeshParams(mesh_filename)};
    auto endIt{tetrahedronMesh.cend()};
    auto tetrahedronNodes{Mesh::getTetrahedronNodesMap(mesh_filename)};
    std::set<size_t> allNodeIDs;
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
        allNodeIDs.insert(nodeIDs.begin(), nodeIDs.end());
    size_t totalNodes{allNodeIDs.size()};

    // Mapping from node ID to it's index in the global stiffness matrix.
    std::unordered_map<size_t, size_t> nodeID_to_globMatrixID;
    size_t index{};
    for (size_t nodeId : allNodeIDs)
        nodeID_to_globMatrixID[nodeId] = index++;

    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
    {
        TetrahedronIndeces globalNodeIndices;
        for (int i{}; i < 4; ++i)
            globalNodeIndices[i] = nodeID_to_globMatrixID[nodeIDs[i]];
        globalNodeIndicesPerElement.emplace_back(globalNodeIndices);

        auto meshParam{std::ranges::find_if(tetrahedronMesh, [tetrahedronID](auto const &param)
                                            { return std::get<0>(param) == tetrahedronID; })};
        if (meshParam != endIt)
        {
            auto const &[basisFuncs, cubWeights]{computeTetrahedronBasisFunctions(*meshParam)};
            allBasisGradients.emplace_back(basisFuncs);
            allCubWeights.emplace_back(cubWeights);
        }
    }

    // Assemblying global stiffness matrix.
    auto globalStiffnessMatrix{assembleGlobalStiffnessMatrixHelper(tetrahedronMesh, allBasisGradients, allCubWeights, totalNodes, globalNodeIndicesPerElement)};

    /* Filling the map. */
    auto const numGlobalEntries{globalStiffnessMatrix.rows()};
    int indexBase{0};
    m_map = Teuchos::rcp(new MapType(numGlobalEntries, indexBase, m_comm));

    auto tpetraMatrix{convertEigenToTpetra(globalStiffnessMatrix)};
    return tpetraMatrix;
}

void GSMatrixAssemblier::setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions)
{
    // Ensure the matrix is in a state that allows adding or replacing entries.
    m_gsmatrix->resumeFill();

    // Setting boundary conditions to global stiffness matrix:
    for (auto const &[nodeID, value] : boundaryConditions)
    {
        size_t numEntries{m_gsmatrix->getNumEntriesInGlobalRow(nodeID)};
        TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
        TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);
        size_t checkNumEntries{};

        // Fetch the current row's structure.
        m_gsmatrix->getGlobalRowCopy(nodeID, indices, values, checkNumEntries);

        // Modify the values array to set the diagonal to 'value' and others to 0
        for (size_t i{}; i < numEntries; i++)
            values[i] = (indices[i] == nodeID) ? value : 0.0; // Set diagonal value to specified value, other - to 0.

        // Replace the modified row back into the matrix.
        m_gsmatrix->replaceGlobalValues(nodeID, indices, values);
    }

    // Finilizing filling of the global stiffness matrix.
    m_gsmatrix->fillComplete();
}
