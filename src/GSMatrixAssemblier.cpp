#include "../include/Utilities/GSMatrixAssemblier.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

#include <set>

static constexpr short _tetrahedronVerticesCount{4};

shards::CellTopology GSMatrixAssemblier::_getTetrahedronCellTopology() const { return shards::getCellTopologyData<shards::Tetrahedron<>>(); }

auto GSMatrixAssemblier::_getBasis() const { return Intrepid2::Basis_HGRAD_TET_Cn_FEM<DeviceType>(m_polynomOrder); }

auto GSMatrixAssemblier::_getCubatureFactory()
{
    // 1. Defining cell topology as tetrahedron.
    auto cellTopology{_getTetrahedronCellTopology()};
    auto basis(_getBasis());
    _countBasisFunctions = basis.getCardinality();

    // 2. Using cubature factory to create cubature function.
    Intrepid2::DefaultCubatureFactory cubFactory;
    return cubFactory.create<DeviceType>(cellTopology, m_desiredAccuracy);
}

void GSMatrixAssemblier::_initializeCubature()
{
    auto cubature{_getCubatureFactory()};       // Generating cubature function.
    _countCubPoints = cubature->getNumPoints(); // Getting number of cubature points.
    _spaceDim = cubature->getDimension();       // Getting dimension (for tetrahedron, obviously - 3D).

    // 1. Allocating memory for cubature points and weights.
    _cubPoints = DynRankView("cubPoints", _countCubPoints, _spaceDim); // Matrix: _countCubPoints x Dimensions.
    _cubWeights = DynRankView("cubWeights", _countCubPoints);          // Vector: _countCubPoints.

    Kokkos::deep_copy(_cubPoints, 0.0);
    Kokkos::deep_copy(_cubWeights, 0.0);

    // 2. Getting cubature points and weights.
    cubature->getCubature(_cubPoints, _cubWeights);

    std::cout << "\n\n"
              << __PRETTY_FUNCTION__ << '\n';
    std::cout << "Cubature points\n";
    for (short i{}; i < _countCubPoints; ++i)
    {
        for (short j{}; j < _spaceDim; ++j)
            std::cout << _cubPoints(i, j) << ' ';
        std::endl(std::cout);
    }
    std::cout << "Cubature weights: ";
    for (short i{}; i < _countCubPoints; ++i)
        std::cout << _cubWeights(i) << ' ';
    std::endl(std::cout);
}

DynRankView GSMatrixAssemblier::_getTetrahedronVertices(MeshTetrahedronParamVector const &meshParams) const
{
    DynRankView vertices("vertices", _countTetrahedra, _tetrahedronVerticesCount, _spaceDim);
    Kokkos::deep_copy(vertices, 0.0);

    size_t i{};
    for (auto const &meshParam : meshParams)
    {
        auto tetrahedron{std::get<1>(meshParam)};
        for (short node{}; node < _tetrahedronVerticesCount; ++node)
        {
            vertices(i, node, 0) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).x());
            vertices(i, node, 1) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).y());
            vertices(i, node, 2) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).z());
        }
        ++i;
    }
    return vertices;
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionValues()
{
    // 2. Allocating memory for values of basis functions.
    DynRankView basisFunctionValues("basisValues", _countBasisFunctions, _countCubPoints);
    Kokkos::deep_copy(basisFunctionValues, 0.0);

    // 3. Calculating basis values on cubature points.
    auto basis{_getBasis()};
    basis.getValues(basisFunctionValues, _cubPoints, Intrepid2::OPERATOR_VALUE);

    return basisFunctionValues;
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionValuesTransformed(MeshTetrahedronParamVector const &meshParams)
{
    auto basisFunctionValues{_computeTetrahedronBasisFunctionValues()};

    DynRankView transformedBasisFunctionValues("transformedBasisValues", _countTetrahedra, _countBasisFunctions, _countCubPoints);
    Kokkos::deep_copy(transformedBasisFunctionValues, 0.0);

    auto vertices{_getTetrahedronVertices(meshParams)};
    auto cellTopology{_getTetrahedronCellTopology()};

    Intrepid2::CellTools<DeviceType>::mapToPhysicalFrame(transformedBasisFunctionValues, _cubPoints, vertices, cellTopology);
    return transformedBasisFunctionValues;
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionGradients()
{
    DynRankView basisGradients("basisGradients", _countBasisFunctions, _countCubPoints, _spaceDim);
    Kokkos::deep_copy(basisGradients, 0.0);

    auto basis{_getBasis()};
    basis.getValues(basisGradients, _cubPoints, Intrepid2::OPERATOR_GRAD);

    std::cout << "\n\n"
              << __PRETTY_FUNCTION__ << '\n';
    for (short i{}; i < _countBasisFunctions; ++i)
    {
        std::cout << std::format("φ_{}\n", i);
        for (short j{}; j < _countCubPoints; ++j)
        {
            for (short k{}; k < _spaceDim; k++)
                std::cout << basisGradients(i, j, k) << ' ';
            std::endl(std::cout);
        }
    }

    return basisGradients;
}

DynRankView GSMatrixAssemblier::_computeCellJacobians(MeshTetrahedronParamVector const &meshParams)
{
    DynRankView jacobians("jacobians", _countTetrahedra, _countCubPoints, _spaceDim, _spaceDim);
    Kokkos::deep_copy(jacobians, 0.0);

    auto vertices{_getTetrahedronVertices(meshParams)};
    auto cellTopology{_getTetrahedronCellTopology()};

    Intrepid2::CellTools<DeviceType>::setJacobian(jacobians, _cubPoints, vertices, cellTopology);

    std::cout << "\n\n"
              << __PRETTY_FUNCTION__ << '\n';
    for (size_t i{}; i < _countTetrahedra; ++i)
    {
        std::cout << std::format("J_{}\n", i);
        for (short j{}; j < _countCubPoints; ++j)
        {
            std::cout << std::format("P_{}\n", j);
            for (short k{}; k < _spaceDim; k++)
            {
                for (short k2{}; k2 < _spaceDim; k2++)
                    std::cout << jacobians(i, j, k, k2) << '\t';
                std::endl(std::cout);
            }
        }
    }
    return jacobians;
}

DynRankView GSMatrixAssemblier::_computeInverseJacobians(DynRankView const &jacobians)
{
    DynRankView invJacobians("invJacobians", _countTetrahedra, _countCubPoints, _spaceDim, _spaceDim);
    Kokkos::deep_copy(invJacobians, 0.0);

    Intrepid2::CellTools<DeviceType>::setJacobianInv(invJacobians, jacobians);
    std::cout << "\n\n"
              << __PRETTY_FUNCTION__ << '\n';
    for (size_t i{}; i < _countTetrahedra; ++i)
    {
        std::cout << std::format("Inv_J_{}\n", i);
        for (short j{}; j < _countCubPoints; ++j)
        {
            std::cout << std::format("P_{}\n", j);
            for (short k{}; k < _spaceDim; k++)
            {
                for (short k2{}; k2 < _spaceDim; k2++)
                    std::cout << invJacobians(i, j, k, k2) << '\t';
                std::endl(std::cout);
            }
        }
    }
    return invJacobians;
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionGradientsTransformed(MeshTetrahedronParamVector const &meshParams)
{
    DynRankView transformedBasisGradients("transformedBasisGradients", _countTetrahedra, _countBasisFunctions, _countCubPoints);
    Kokkos::deep_copy(transformedBasisGradients, 0.0);

    auto basisGradients{_computeTetrahedronBasisFunctionGradients()};
    auto jacobians{_computeCellJacobians(meshParams)};
    auto invJacobians{_computeInverseJacobians(jacobians)};

    Intrepid2::FunctionSpaceTools<DeviceType>::HGRADtransformGRAD(transformedBasisGradients, invJacobians, basisGradients);

    std::cout << "\n\n"
              << __PRETTY_FUNCTION__ << '\n';
    for (size_t i{}; i < _countTetrahedra; ++i)
    {
        std::cout << std::format("Tetrahedron[{}]\n", i);
        for (short j{}; j < _countBasisFunctions; ++j)
        {
            std::cout << std::format("φ_{}: ", j);
            for (short k{}; k < _countCubPoints; ++k)
                std::cout << transformedBasisGradients(i, j, k) << ' ';
            std::endl(std::cout);
        }
    }
    return transformedBasisGradients;
}

DynRankView GSMatrixAssemblier::_computeLocalStiffnessMatrices(DynRankView const &basisGradients) const
{
    DynRankView localStiffnessMatrices("localStiffnessMatrices", _countTetrahedra, _countBasisFunctions, _countBasisFunctions); // Creating local stiffness matrix.
    Kokkos::deep_copy(localStiffnessMatrices, 0.0);                                                                             // Initialization of local stiffness matrix with nulls.

    // 2. Calculating local stiffness matrix.
    for (size_t tetraId{}; tetraId < _countTetrahedra; ++tetraId)
        for (int i{}; i < _countBasisFunctions; ++i)
            for (int j{}; j < _countBasisFunctions; ++j)
                for (int qp{}; qp < _countCubPoints; ++qp)
                {
                    double gradDotProduct{};
                    for (short d{}; d < _spaceDim; ++d)
                        gradDotProduct += basisGradients(tetraId, i, qp, d) * basisGradients(tetraId, j, qp, d);
                    localStiffnessMatrices(tetraId, i, j) += gradDotProduct * _cubWeights(qp);
                }
    return localStiffnessMatrices;
}

std::vector<GSMatrixAssemblier::MatrixEntry> GSMatrixAssemblier::_getMatrixEntries(DynRankView const &basisGradients,
                                                                                   TetrahedronIndicesVector const &globalNodeIndicesPerElement)
{
    // 1. Getting all LSMs.
    auto localStiffnessMatrices{_computeLocalStiffnessMatrices(basisGradients)};

    std::cout << "\n\nLocal stiffness matrices\n";
    for (size_t i{}; i < _countTetrahedra; ++i)
    {
        std::cout << std::format("LSM of tetrahedron[{}]\n", i);
        for (short j{}; j < _countBasisFunctions; ++j)
        {
            for (short k{}; k < _countBasisFunctions; ++k)
                std::cout << localStiffnessMatrices(i, j, k) << ' ';
            std::endl(std::cout);
        }
    }

    // 2. Counting basis functions per node.
    auto countBasisFuncsPerNode{_countBasisFunctions / _tetrahedronVerticesCount};
    std::cout << "Count basis funcs per node: " << countBasisFuncsPerNode << '\n';

    // 3. Filling matrix entries.
    std::vector<GSMatrixAssemblier::MatrixEntry> matrixEntries;
    try
    {
        for (size_t tetraId{}; tetraId < globalNodeIndicesPerElement.size(); ++tetraId)
        {
            auto const &nodeIndices{globalNodeIndicesPerElement.at(tetraId)};
            for (size_t localNodeI{}; localNodeI < _tetrahedronVerticesCount; ++localNodeI)
            {
                for (size_t localNodeJ{}; localNodeJ < _tetrahedronVerticesCount; ++localNodeJ)
                {
                    for (int basisI{}; basisI < countBasisFuncsPerNode; ++basisI)
                    {
                        for (int basisJ{}; basisJ < countBasisFuncsPerNode; ++basisJ)
                        {
                            auto i{localNodeI * countBasisFuncsPerNode + basisI},
                                j{localNodeJ * countBasisFuncsPerNode + basisJ};

                            Scalar value{localStiffnessMatrices(tetraId, i, j)};
                            GlobalOrdinal globalRow{nodeIndices[localNodeI] * countBasisFuncsPerNode + basisI},
                                globalCol{nodeIndices[localNodeJ] * countBasisFuncsPerNode + basisJ};

                            matrixEntries.push_back({globalRow, globalCol, value});
                        }
                    }
                }
            }
        }
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error occured.");
    }

    if (matrixEntries.empty())
        WARNINGMSG("Something went wrong while filling matrix entries - matrix entries are empty - there is no elements.");

    return matrixEntries;
}

auto GSMatrixAssemblier::_assemblyGlobalStiffnessMatrixHelper(DynRankView const &basisGradients,
                                                              TetrahedronIndicesVector const &globalNodeIndicesPerElement)
{
    try
    {
        // 1. Getting all matrix entries.
        auto matrixEntries{_getMatrixEntries(basisGradients, globalNodeIndicesPerElement)};

        // 2. Getting unique global indeces.
        std::set<GlobalOrdinal> globalIndeces;
        std::map<GlobalOrdinal, std::set<GlobalOrdinal>> graphEntries;
        for (auto const &entry : matrixEntries)
        {
            globalIndeces.insert(entry.row);
            graphEntries[entry.row].insert(entry.col);
        }

        // 3. Initializing all necessary variables.
        short indexBase{0};
        auto countGlobalNodes{globalIndeces.size()};

        // 4. Calculating count of entries per row.
        std::map<GlobalOrdinal, size_t> numConnections;
        for (auto const &[node, connections] : graphEntries)
            numConnections[node] = connections.size();

        Teuchos::RCP<Tpetra::CrsGraph<>> graph;
        try
        {
            // 4. Initializing tpetra map.
            m_map = Teuchos::rcp(new MapType(countGlobalNodes, indexBase, m_comm));

            // 5. Initializing tpetra graph.
            std::vector<size_t> numEntriesPerRow(countGlobalNodes);
            for (auto const &rowEntry : graphEntries)
                numEntriesPerRow[m_map->getLocalElement(rowEntry.first)] = rowEntry.second.size();
            Teuchos::ArrayView<size_t const> entriesPerRowView(numEntriesPerRow.data(), numEntriesPerRow.size());
            graph = Teuchos::rcp(new Tpetra::CrsGraph<>(m_map, entriesPerRowView));
            for (auto const &rowEntries : graphEntries)
            {
                std::vector<GlobalOrdinal> columns(rowEntries.second.begin(), rowEntries.second.end());
                Teuchos::ArrayView<GlobalOrdinal const> colsView(columns.data(), columns.size());
                graph->insertGlobalIndices(rowEntries.first, colsView);
            }
            graph->fillComplete();
        }
        catch (std::exception const &ex)
        {
            ERRMSG(ex.what());
        }
        catch (...)
        {
            ERRMSG("Unknown error occured while filling tpetra gpaph.");
        }

        // 6. Initializing GSM.
        auto globalStiffnessMatrix{Teuchos::rcp(new TpetraMatrixType(graph))};

        // 7. Adding local stiffness matrices to the global.
        try
        {
            for (auto const &entry : matrixEntries)
            {
                Teuchos::ArrayView<GlobalOrdinal const> colsView(std::addressof(entry.col), 1);
                Teuchos::ArrayView<Scalar const> valsView(std::addressof(entry.value), 1);
                globalStiffnessMatrix->sumIntoGlobalValues(entry.row, colsView, valsView);
            }

            // 8. Filling completion.
            globalStiffnessMatrix->fillComplete();
        }
        catch (std::exception const &ex)
        {
            ERRMSG(ex.what());
        }
        catch (...)
        {
            ERRMSG("Unknown error occured while assemblying global stiffness matrix from local stiffness matrices.");
        }
        return globalStiffnessMatrix;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error occured while assemblying global stiffness matrix. Probably solution: decrease polynom order or desired accuracy.");
    }
    WARNINGMSG("Returning empty global stiffness matrix. Check that everything is fine in indexing, all sizes, polynom order/accuracy, etc.");
    return Teuchos::rcp(new TpetraMatrixType(m_map, 0));
}

GSMatrixAssemblier::GSMatrixAssemblier(std::string_view mesh_filename, int polynomOrder, int desiredCalculationAccuracy)
    : m_meshfilename(mesh_filename), m_comm(Tpetra::getDefaultComm()),
      m_polynomOrder(polynomOrder), m_desiredAccuracy(desiredCalculationAccuracy)
{
    _initializeCubature();
    m_gsmatrix = assembleGlobalStiffnessMatrix(m_meshfilename);
}

Teuchos::RCP<TpetraMatrixType> GSMatrixAssemblier::assembleGlobalStiffnessMatrix(std::string_view mesh_filename)
{
    TetrahedronIndicesVector globalNodeIndicesPerElement;

    // 1. Getting all necessary tetrahedron parameters.
    auto tetrahedronMesh{Mesh::getTetrahedronMeshParams(mesh_filename)};
    _countTetrahedra = tetrahedronMesh.size();
    auto endIt{tetrahedronMesh.cend()};
    auto tetrahedronNodes{Mesh::getTetrahedronNodesMap(mesh_filename)};

    // 2. Counting only unique nodes.
    std::set<size_t> allNodeIDs;
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
        allNodeIDs.insert(nodeIDs.begin(), nodeIDs.end());

    // 3. Filling global indices.
    for (auto const &[tetrahedronID, nodeIDs] : tetrahedronNodes)
    {
        std::array<LocalOrdinal, 4ul> nodes;
        for (short i{}; i < _tetrahedronVerticesCount; ++i)
            nodes[i] = nodeIDs[i] - 1;
        globalNodeIndicesPerElement.emplace_back(nodes);
    }

    // 4. Computing all basis gradients and cubature weights.
    auto basisGradients{_computeTetrahedronBasisFunctionGradientsTransformed(tetrahedronMesh)};

    // 5. Assemblying global stiffness matrix.
    return _assemblyGlobalStiffnessMatrixHelper(basisGradients, globalNodeIndicesPerElement);
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
        for (size_t i{}; i < numEntries; ++i)
            if (indices[i] == nodeID)
                return values[i];
    }

    // If the column index was not found in the row, the element is assumed to be zero (sparse matrix property).
    return Scalar(0.0);
}

void GSMatrixAssemblier::setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions)
{
    if (boundaryConditions.empty())
        return;

    // 1. Ensure the matrix is in a state that allows adding or replacing entries.
    m_gsmatrix->resumeFill();

    // 2. Setting boundary conditions to global stiffness matrix:
    for (auto const &[nodeInGmsh, value] : boundaryConditions)
    {
        auto nodeID{nodeInGmsh - 1}; // In the program node id is less on 1.

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
                    std::cout << "(" << indices[k] << ", " << std::scientific << std::setprecision(2) << values[k] << ") ";
                std::endl(std::cout);
            }
        }
        // Synchronize all processes.
        m_comm->barrier();
    }
    m_comm->barrier();
}
