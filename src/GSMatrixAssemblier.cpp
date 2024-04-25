#include "../include/FiniteElementMethod/GSMatrixAssemblier.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

Scalar getValueFromMatrix(Teuchos::RCP<TpetraMatrixType> const &matrix, GlobalOrdinal row, GlobalOrdinal col)
{
    try
    {
        size_t numEntries{matrix->getNumEntriesInGlobalRow(row)};
        if (numEntries == 0ul)
        {
            WARNINGMSG("Global stiffness matrix is empty");
            return -1ul;
        }

        TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
        TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);

        size_t checkNumEntries{};
        matrix->getGlobalRowCopy(row, indices, values, checkNumEntries);

        for (size_t i{}; i < indices.size(); ++i)
            if (indices[i] == col)
                return values[i];

        WARNINGMSG(util::stringify("No entry found at [", row, "][", col, "]. Returning ", -1ul << '\n'));
        return -1ul;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    return -1ul;
}

void printGraph(Teuchos::RCP<Tpetra::CrsGraph<>> const &graph)
{
    try
    {
        std::cout << "\n\nGraph data:\n";
        Teuchos::RCP<MapType const> rowMap{graph->getRowMap()};
        size_t numLocalRows{rowMap->getGlobalNumElements()};

        for (size_t i{}; i < numLocalRows; ++i)
        {
            GlobalOrdinal globalRow{rowMap->getGlobalElement(i)};
            size_t numEntries{graph->getNumEntriesInGlobalRow(globalRow)};
            TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);

            size_t numIndices;
            graph->getGlobalRowCopy(globalRow, indices, numIndices);

            // Print row and its connections
            std::cout << "Row " << globalRow << ": ";
            for (size_t j{}; j < numIndices; ++j)
                std::cout << indices[j] << " ";
            std::cout << std::endl;
        }
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
}

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
    try
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
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }

#ifdef PRINT_ALL
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
#endif
}

DynRankView GSMatrixAssemblier::_getTetrahedronVertices(MeshTetrahedronParamVector const &meshParams) const
{
    try
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
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array with vertices of the all tetrahedrons from the mesh");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionValues()
{
    try
    {
        // 1. Allocating memory for values of basis functions.
        DynRankView basisFunctionValues("basisValues", _countBasisFunctions, _countCubPoints);
        Kokkos::deep_copy(basisFunctionValues, 0.0);

        // 2. Calculating basis values on cubature points.
        auto basis{_getBasis()};
        basis.getValues(basisFunctionValues, _cubPoints, Intrepid2::OPERATOR_VALUE);

        return basisFunctionValues;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for basis function values");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionValuesTransformed(MeshTetrahedronParamVector const &meshParams)
{
    try
    {
        auto basisFunctionValues{_computeTetrahedronBasisFunctionValues()};

        DynRankView transformedBasisFunctionValues("transformedBasisValues", _countTetrahedra, _countBasisFunctions, _countCubPoints);
        Kokkos::deep_copy(transformedBasisFunctionValues, 0.0);

        auto vertices{_getTetrahedronVertices(meshParams)};
        auto cellTopology{_getTetrahedronCellTopology()};

        Intrepid2::CellTools<DeviceType>::mapToPhysicalFrame(transformedBasisFunctionValues, _cubPoints, vertices, cellTopology);
        return transformedBasisFunctionValues;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for basis function values that are transformed to physical space");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionGradients()
{
    try
    {
        DynRankView basisGradients("basisGradients", _countBasisFunctions, _countCubPoints, _spaceDim);
        Kokkos::deep_copy(basisGradients, 0.0);

        auto basis{_getBasis()};
        basis.getValues(basisGradients, _cubPoints, Intrepid2::OPERATOR_GRAD);

#ifdef PRINT_ALL
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
#endif
        return basisGradients;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for gradients of basis function");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeCellJacobians(MeshTetrahedronParamVector const &meshParams)
{
    try
    {
        DynRankView jacobians("jacobians", _countTetrahedra, _countCubPoints, _spaceDim, _spaceDim);
        Kokkos::deep_copy(jacobians, 0.0);

        auto vertices{_getTetrahedronVertices(meshParams)};
        auto cellTopology{_getTetrahedronCellTopology()};

        Intrepid2::CellTools<DeviceType>::setJacobian(jacobians, _cubPoints, vertices, cellTopology);

#ifdef PRINT_ALL
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
#endif
        return jacobians;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for cell jacobians");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeInverseJacobians(DynRankView const &jacobians)
{
    try
    {
        DynRankView invJacobians("invJacobians", _countTetrahedra, _countCubPoints, _spaceDim, _spaceDim);
        Kokkos::deep_copy(invJacobians, 0.0);

        Intrepid2::CellTools<DeviceType>::setJacobianInv(invJacobians, jacobians);

#ifdef PRINT_ALL
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
#endif
        return invJacobians;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for inversed cell jacobians");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeTetrahedronBasisFunctionGradientsTransformed(MeshTetrahedronParamVector const &meshParams)
{
    try
    {
        DynRankView transformedBasisGradients("transformedBasisGradients", _countTetrahedra, _countBasisFunctions, _countCubPoints, _spaceDim);
        Kokkos::deep_copy(transformedBasisGradients, 0.0);

        auto basisGradients{_computeTetrahedronBasisFunctionGradients()};
        auto jacobians{_computeCellJacobians(meshParams)};
        auto invJacobians{_computeInverseJacobians(jacobians)};

        Intrepid2::FunctionSpaceTools<DeviceType>::HGRADtransformGRAD(transformedBasisGradients, invJacobians, basisGradients);

#ifdef PRINT_ALL
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
#endif
        return transformedBasisGradients;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for gradients of basis function that are transformed to physical space");
    return DynRankView();
}

DynRankView GSMatrixAssemblier::_computeLocalStiffnessMatrices(DynRankView const &basisGradients) const
{
    try
    {
        DynRankView localStiffnessMatrices("localStiffnessMatrices", _countTetrahedra, _countBasisFunctions, _countBasisFunctions);
        Kokkos::deep_copy(localStiffnessMatrices, 0.0);

        // 1. Calculating local stiffness matrix.
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
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error");
    }
    WARNINGMSG("Returning empty multidimensional array which was intended for LSM (Local Stiffness Matrix)");
    return DynRankView();
}

std::vector<GSMatrixAssemblier::MatrixEntry> GSMatrixAssemblier::_getMatrixEntries(DynRankView const &basisGradients,
                                                                                   TetrahedronIndicesVector const &globalNodeIndicesPerElement)
{
    // 1. Getting all LSMs.
    auto localStiffnessMatrices{_computeLocalStiffnessMatrices(basisGradients)};

    // 2. Counting basis functions per node.
    auto countBasisFuncsPerNode{_countBasisFunctions / _tetrahedronVerticesCount};

#ifdef PRINT_ALL
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
    std::cout << "Count basis funcs per node: " << countBasisFuncsPerNode << '\n';
#endif

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

#ifdef PRINT_ALL
                            std::cout << std::format("[{}][{}]: {}\n", globalRow, globalCol, value);
#endif
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
        ERRMSG("Unknown error was occured");
    }

    if (matrixEntries.empty())
        WARNINGMSG("Something went wrong while filling matrix entries - matrix entries are empty - there is no elements");

    return matrixEntries;
}

void GSMatrixAssemblier::_assemblyGlobalStiffnessMatrixHelper(DynRankView const &basisGradients,
                                                              TetrahedronIndicesVector const &globalNodeIndicesPerElement)
{
    try
    {
        // 1. Getting all matrix entries.
        auto matrixEntries{_getMatrixEntries(basisGradients, globalNodeIndicesPerElement)};

        // 2. Getting unique global entries.
        std::map<GlobalOrdinal, std::set<GlobalOrdinal>> graphEntries;
        try
        {
            for (auto const &entry : matrixEntries)
                graphEntries[entry.row].insert(entry.col);
        }
        catch (std::exception const &ex)
        {
            ERRMSG(ex.what());
        }
        catch (...)
        {
            std::cout << "Unknown error\n";
        }

#ifdef PRINT_ALL
        std::cout << "\n\n\nGraph entries\n";
        for (auto const &[globalId, colIds] : graphEntries)
        {
            std::cout << "Global ID (" << globalId << "): ";
            for (size_t colId : colIds)
                std::cout << colId << ' ';
            std::endl(std::cout);
        }
#endif

        // 3. Initializing all necessary variables.
        short indexBase{0};
        auto countGlobalNodes{graphEntries.size()};

#ifdef PRINT_ALL
        std::cout << "Count of global nodes: " << countGlobalNodes << '\n';
#endif

        // 4. Initializing tpetra map.
        m_map = Teuchos::rcp(new MapType(countGlobalNodes, indexBase, m_comm));

        // 5. Initializing tpetra graph.
        std::vector<size_t> numEntriesPerRow(countGlobalNodes);
        for (auto const &rowEntry : graphEntries)
            numEntriesPerRow.at(m_map->getLocalElement(rowEntry.first)) = rowEntry.second.size();

#ifdef PRINT_ALL
        std::cout << "\n\n\nNumber of entries per row\n";
        size_t rowId{};
        for (size_t entriesPerRow : numEntriesPerRow)
            std::cout << rowId++ << ": " << entriesPerRow << '\n';
#endif

        Teuchos::RCP<Tpetra::CrsGraph<>> graph{
            Teuchos::rcp(new Tpetra::CrsGraph<>(m_map, Teuchos::ArrayView<size_t const>(numEntriesPerRow.data(), numEntriesPerRow.size())))};
        for (auto const &rowEntries : graphEntries)
        {
            std::vector<GlobalOrdinal> columns(rowEntries.second.begin(), rowEntries.second.end());
            Teuchos::ArrayView<GlobalOrdinal const> colsView(columns.data(), columns.size());
            graph->insertGlobalIndices(rowEntries.first, colsView);
        }
        graph->fillComplete();

#ifdef PRINT_ALL
        printGraph(graph);
#endif

        // 6. Initializing GSM.
        m_gsmatrix = Teuchos::rcp(new TpetraMatrixType(graph));

        // 7. Adding local stiffness matrices to the global.
#ifdef PRINT_ALL
        std::cout << "Summarizing values from LSM to GSM\n";
#endif

        for (auto const &entry : matrixEntries)
        {
#ifdef PRINT_ALL
            std::cout << std::format("Before sum: [{}][{}]: {} + {}\n", entry.row, entry.col,
                                     getValueFromMatrix(m_gsmatrix, entry.row, entry.col), entry.value);
#endif

            Teuchos::ArrayView<GlobalOrdinal const> colsView(std::addressof(entry.col), 1);
            Teuchos::ArrayView<Scalar const> valsView(std::addressof(entry.value), 1);
            m_gsmatrix->sumIntoGlobalValues(entry.row, colsView, valsView);

#ifdef PRINT_ALL
            std::cout << std::format("After sum: [{}][{}]: {}\n", entry.row, entry.col,
                                     getValueFromMatrix(m_gsmatrix, entry.row, entry.col));
#endif
        }

        // 8. Filling completion.
        m_gsmatrix->fillComplete();
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while assemblying global stiffness matrix. Probably solution: decrease polynom order or desired accuracy");
    }
}

void GSMatrixAssemblier::_setBoundaryConditionForNode(LocalOrdinal nodeID, Scalar value)
{
    size_t numEntries{m_gsmatrix->getNumEntriesInGlobalRow(nodeID)};
    TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
    TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);
    size_t checkNumEntries{};

    // 1. Fetch the current row's structure.
    m_gsmatrix->getGlobalRowCopy(nodeID, indices, values, checkNumEntries);

    // 2. Modify the values array to set the diagonal to 'value' and others to 0
    for (size_t i{}; i < numEntries; i++)
        values[i] = (indices[i] == nodeID) ? value : 0.0; // Set diagonal value to specified value, other - to 0.

    // 3. Replace the modified row back into the matrix.
    m_gsmatrix->replaceGlobalValues(nodeID, indices, values);
}

GSMatrixAssemblier::GSMatrixAssemblier(std::string_view mesh_filename, short polynomOrder, short desiredCalculationAccuracy)
    : m_meshfilename(mesh_filename), m_comm(Tpetra::getDefaultComm()),
      m_polynomOrder(polynomOrder), m_desiredAccuracy(desiredCalculationAccuracy)
{
    if (polynomOrder <= 0)
    {
        ERRMSG("Polynom order can't be negative or equals to 0");
        throw std::runtime_error("Polynom order can't be negative or equals to 0");
    }
    if (desiredCalculationAccuracy <= 0)
    {
        ERRMSG("Desired calculation accuracy can't be negative or equals to 0");
        throw std::runtime_error("Desired calculation accuracy can't be negative or equals to 0");
    }

    _initializeCubature();
    assembleGlobalStiffnessMatrix(m_meshfilename);
}

void GSMatrixAssemblier::assembleGlobalStiffnessMatrix(std::string_view mesh_filename)
{
    TetrahedronIndicesVector globalNodeIndicesPerElement;

    // 1. Getting all necessary tetrahedron parameters.
    auto tetrahedronMesh{Mesh::getTetrahedronMeshParams(mesh_filename)};
    if (tetrahedronMesh.empty())
        throw std::runtime_error(util::stringify("Can't get mesh parameters from file ", mesh_filename));

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
    _assemblyGlobalStiffnessMatrixHelper(basisGradients, globalNodeIndicesPerElement);
}

bool GSMatrixAssemblier::empty() const { return m_gsmatrix->getGlobalNumEntries() == 0; }

Scalar GSMatrixAssemblier::getValueFromGSM(GlobalOrdinal row, GlobalOrdinal col) const { return getValueFromMatrix(m_gsmatrix, row, col); }

void GSMatrixAssemblier::setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions)
{
    if (boundaryConditions.empty())
    {
        WARNINGMSG("Boundary conditions are empty, check them, maybe you forgot to fill them");
        return;
    }

    if (empty())
    {
        ERRMSG("Can't set boundary conditions. Matrix is uninitialized/empty, there are no any entries");
        return;
    }

    try
    {
        // 1. Ensure the matrix is in a state that allows adding or replacing entries.
        m_gsmatrix->resumeFill();

        // 2. Setting boundary conditions to global stiffness matrix:
        int DOF_per_node{m_polynomOrder};
        for (auto const &[nodeInGmsh, value] : boundaryConditions)
        {
            for (int j{}; j < DOF_per_node; ++j)
            {
                LocalOrdinal nodeID{(nodeInGmsh - 1) * DOF_per_node + j};

                if (nodeID >= static_cast<LocalOrdinal>(rows()))
                    throw std::runtime_error(util::stringify("Boundary condition refers to node index ",
                                                             nodeID,
                                                             ", which exceeds the maximum row index of ",
                                                             rows() - 1, "."));

                _setBoundaryConditionForNode(nodeID, value);
            }
        }

        // 4. Finilizing filling of the global stiffness matrix.
        m_gsmatrix->fillComplete();
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while trying to apply boundary conditions on global stiffness matrix");
    }
}

void GSMatrixAssemblier::print() const
{
    if (empty())
    {
        WARNINGMSG("Matrix is empty, nothing to print");
        return;
    }

    try
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
                        std::cout << "(" << indices[k] << ", " << values[k] << ") ";
                    std::endl(std::cout);
                }
            }
            // Synchronize all processes.
            m_comm->barrier();
        }
        m_comm->barrier();
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while printing global stiffness matrix");
    }
}
