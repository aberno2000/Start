#include "../include/Utilities/GSMatrixAssemblier.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

BasisFuncValues_CubatureWeights GSMatrixAssemblier::computeTetrahedronBasisFunctions(MeshTetrahedronParam const &meshParam) const
{
    // 1. Defining cell topology as tetrahedron.
    shards::CellTopology cellTopology{shards::getCellTopologyData<shards::Tetrahedron<>>()};
    Intrepid2::Basis_HGRAD_TET_C1_FEM<DeviceType> basis;

    // 2. Using cubature factory to create cubature function.
    Intrepid2::DefaultCubatureFactory cubFactory;
    auto cubature{cubFactory.create<DeviceType>(cellTopology, basis.getDegree())};

    auto numCubPoints{cubature->getNumPoints()}; // Getting number of cubature points.
    auto spaceDim{cubature->getDimension()};     // Getting dimension (for tetrahedron, obviously - 3D).

    // 3. Allocating memory for cubature poinst and weights.
    DynRankView cubPoints("cubPoints", numCubPoints, spaceDim);
    DynRankView cubWeights("cubWeights", numCubPoints);

    // 4. Allocating memory for values of basis functions.
    auto numFields{basis.getCardinality()};
    DynRankView basisValues("basisValues", numFields, numCubPoints);
    DynRankView transformedBasisValues("transformedBasisValues", 1, numFields, numCubPoints);

    // 5. Getting cubature points and weights.
    cubature->getCubature(cubPoints, cubWeights);

    // 6. Getting tetrahedron coordinates of each vertex.
    DynRankView vertices("vertices", 1, 4, 3);
    auto tetrahedron{std::get<1>(meshParam)};
    for (short node{}; node < 4; ++node)
    {
        vertices(0, node, 0) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).x());
        vertices(0, node, 1) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).y());
        vertices(0, node, 2) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).z());
    }

    // 7. Calculating basis functions on cubature points.
    basis.getValues(basisValues, cubPoints, Intrepid2::OPERATOR_VALUE);
    DynRankViewVector basisFunctionsValues;
    for (LocalOrdinal i{}; i < numFields; ++i)
    {
        DynRankView fieldValues("fieldValues", numCubPoints);
        for (LocalOrdinal j{}; j < numCubPoints; ++j)
            fieldValues(j) = basisValues(i, j);
        basisFunctionsValues.emplace_back(fieldValues);
    }

    // 8. Transforming basis functions from relative values to physical space.
    Intrepid2::CellTools<DeviceType>::mapToPhysicalFrame(transformedBasisValues, cubPoints, vertices, cellTopology);

#ifdef PRINT_ALL
    // 8_opt: printing transformed basis values in all cubature points.
    for (LocalOrdinal i{}; i < numFields; ++i)
        for (LocalOrdinal j{}; j < numCubPoints; ++j)
            std::cout << std::format("Tetrahedron[{}]: Transformed basis function {} at cubature point {} = {}\n",
                                     std::get<0>(meshParam), i, j, transformedBasisValues(0, i, j));
#endif

    return std::make_pair(basisFunctionsValues, cubWeights);
}

DynRankView GSMatrixAssemblier::computeLocalStiffnessMatrix(DynRankViewVector const &basisGradients, DynRankView const &cubWeights) const
{
    // 1. Getting count of basis functions and count of cubature points.
    auto const numFields{basisGradients.size()};
    auto const numCubPoints{cubWeights.extent(0)};

    DynRankView localStiffnessMatrix("localStiffnessMatrix", numFields, numFields); // Creating local stiffness matrix.
    Kokkos::deep_copy(localStiffnessMatrix, 0.0);                                   // Initialization of local stiffness matrix with nulls.

    // 2. Calculating local stiffness matrix.
    for (size_t i{}; i < numFields; ++i)
        for (size_t j{}; j < numFields; ++j)
            for (size_t qp{}; qp < numCubPoints; ++qp)
                for (short d{}; d < 3; ++d)
                    localStiffnessMatrix(i, j) += basisGradients[i](qp, d) * basisGradients[j](qp, d) * cubWeights(qp);

#ifdef PRINT_ALL
    // 2_opt. Printing local stiffness matrix.
    printDynRankView(localStiffnessMatrix);
#endif

    return localStiffnessMatrix;
}

EigenSparseMatrix GSMatrixAssemblier::assembleGlobalStiffnessMatrixHelper(
    MeshTetrahedronParamVector const &meshParams,
    DynRankViewMatrix const &allBasisGradients,
    DynRankViewVector const &allCubWeights,
    GlobalOrdinal totalNodes,
    TetrahedronIndicesVector const &globalNodeIndicesPerElement) const
{
    // 1. Initialization of the global stiffness matrix.
    EigenSparseMatrix globalStiffnessMatrix(totalNodes, totalNodes);

    // 2. List for store non-null elements.
    EigenTripletVector tripletList;
    for (size_t elemIndex{}; elemIndex < meshParams.size(); ++elemIndex)
    {
        // 2_1. Calculating local stiffness matrix.
        auto localStiffnessMatrix{computeLocalStiffnessMatrix(allBasisGradients[elemIndex], allCubWeights[elemIndex])};

        // 2_2. Indices of global nodes for the current tetrahedron.
        auto const &globalNodeIndices{globalNodeIndicesPerElement[elemIndex]};

        // 2_3. Adding local stiffness matrix to the global.
        for (short i{}; i < 4; ++i)
            for (short j{}; j < 4; ++j)
                tripletList.emplace_back(
                    globalNodeIndices[i],
                    globalNodeIndices[j],
                    localStiffnessMatrix(i, j));
    }

    // 3. Assemblying global matrix from the triplets.
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
        std::endl(std::cout);
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
    TetrahedronIndicesVector globalNodeIndicesPerElement;
    DynRankViewMatrix allBasisGradients;
    DynRankViewVector allCubWeights;

    // 1. Getting all necessary tetrahedron parameters.
    auto tetrahedronMesh{Mesh::getTetrahedronMeshParams(mesh_filename)};
    auto endIt{tetrahedronMesh.cend()};
    auto tetrahedronNodes{Mesh::getTetrahedronNodesMap(mesh_filename)};

    // 2. Counting only unique nodes.
    std::set<size_t> allNodeIDs;
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
        allNodeIDs.insert(nodeIDs.begin(), nodeIDs.end());
    size_t totalNodes{allNodeIDs.size()};

    // 3. Filling global indices.
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
    {
        std::array<LocalOrdinal, 4ul> nodes;
        for (short i{}; i < 4; ++i)
            nodes[i] = nodeIDs[i] - 1;
        globalNodeIndicesPerElement.emplace_back(nodes);
    }

    // 4. Computing all basis gradients and cubature weights.
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
    {
        auto meshParam{std::ranges::find_if(tetrahedronMesh, [tetrahedronID](auto const &param)
                                            { return std::get<0>(param) == tetrahedronID; })};
        if (meshParam != endIt)
        {
            auto const &[basisFuncs, cubWeights]{computeTetrahedronBasisFunctions(*meshParam)};
            allBasisGradients.emplace_back(basisFuncs);
            allCubWeights.emplace_back(cubWeights);
        }
    }

    // 5. Assemblying global stiffness matrix.
    auto globalStiffnessMatrix{assembleGlobalStiffnessMatrixHelper(tetrahedronMesh, allBasisGradients, allCubWeights, totalNodes, globalNodeIndicesPerElement)};

    // 6*. Filling the Trilinos map.
    auto const numGlobalEntries{globalStiffnessMatrix.rows()};
    int indexBase{0};
    m_map = Teuchos::rcp(new MapType(numGlobalEntries, indexBase, m_comm));

    // 7. Converting Eigen sparse matrix to Tpetra sparse matrix.
    auto tpetraMatrix{convertEigenToTpetra(globalStiffnessMatrix)};
    return tpetraMatrix;
}

Scalar GSMatrixAssemblier::getScalarFieldValue(GlobalOrdinal nodeID) const
{
    size_t numEntries{m_gsmatrix->getNumEntriesInGlobalRow(nodeID)};
    if (numEntries > 0)
    {
        TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
        TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);

        m_gsmatrix->getGlobalRowCopy(nodeID, indices, values, numEntries);

        // Search for the column index in the retrieved row.
        for (size_t i = 0; i < numEntries; ++i)
            if (indices[i] == nodeID)
                return values[i];
    }

    // If the column index was not found in the row, the element is assumed to be zero (sparse matrix property).
    return Scalar(0.0);
}

void GSMatrixAssemblier::setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions)
{
    // 1. Ensure the matrix is in a state that allows adding or replacing entries.
    m_gsmatrix->resumeFill();

    // 2. Setting boundary conditions to global stiffness matrix:
    for (auto const &[nodeID, value] : boundaryConditions)
    {
        size_t numEntries{m_gsmatrix->getNumEntriesInGlobalRow(nodeID)};
        TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
        TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);
        size_t checkNumEntries{};

        // 2_1. Fetch the current row's structure.
        m_gsmatrix->getGlobalRowCopy(nodeID, indices, values, checkNumEntries);

        // 2_2. Modify the values array to set the diagonal to 'value' and others to 0
        for (size_t i{}; i < numEntries; i++)
            values[i] = (indices[i] == nodeID) ? value : 0.0; // Set diagonal value to specified value, other - to 0.

        // 2_3. Replace the modified row back into the matrix.
        m_gsmatrix->replaceGlobalValues(nodeID, indices, values);
    }

    // 3. Finilizing filling of the global stiffness matrix.
    m_gsmatrix->fillComplete();
}
