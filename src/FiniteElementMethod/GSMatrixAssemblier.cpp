#include "../include/FiniteElementMethod/GSMatrixAssemblier.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

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

shards::CellTopology GSMatrixAssemblier::_getTetrahedronCellTopology() const { return shards::getCellTopologyData<shards::Tetrahedron<>>(); }

auto GSMatrixAssemblier::_getBasis() const { return Intrepid2::Basis_HGRAD_TET_C1_FEM<DeviceType>(); }

void GSMatrixAssemblier::_initializeCubature()
{
    try
    {
        // 1. Defining cell topology as tetrahedron.
        auto cellTopology{_getTetrahedronCellTopology()};
        auto basis{Intrepid2::Basis_HGRAD_TET_C1_FEM<DeviceType>()};
        _countBasisFunctions = basis.getCardinality(); // For linear tetrahedrons (polynom order = 1) count of basis functions = 4 (4 verteces, 4 basis functions).

        // 2. Using cubature factory to create cubature function.
        Intrepid2::DefaultCubatureFactory cubFactory;
        auto cubature{cubFactory.create<DeviceType>(cellTopology, m_desiredAccuracy)}; // Generating cubature function.
        _countCubPoints = cubature->getNumPoints();                                    // Getting number of cubature points.

        // 1. Allocating memory for cubature points and weights.
        _cubPoints = DynRankView("cubPoints", _countCubPoints, kdefault_space_dim); // Matrix: _countCubPoints x Dimensions.
        _cubWeights = DynRankView("cubWeights", _countCubPoints);                   // Vector: _countCubPoints.

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
}

DynRankView GSMatrixAssemblier::_getTetrahedronVertices()
{
    try
    {
        DynRankView vertices("vertices", getMeshComponents().size(), kdefault_tetrahedron_vertices_count, kdefault_space_dim);
        Kokkos::deep_copy(vertices, 0.0);

        size_t i{};
        for (auto const &meshParam : getMeshComponents().getMeshComponents())
        {
            auto tetrahedron{meshParam.tetrahedron};
            for (short node{}; node < kdefault_tetrahedron_vertices_count; ++node)
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

DynRankView GSMatrixAssemblier::_computeLocalStiffnessMatrices()
{
    try
    {
        // 1. Calculating basis gradients.
        DynRankView referenceBasisGrads("referenceBasisGrads", _countBasisFunctions, _countCubPoints, kdefault_space_dim);
        Kokkos::deep_copy(referenceBasisGrads, 0.0);
        auto basis{_getBasis()};
        basis.getValues(referenceBasisGrads, _cubPoints, Intrepid2::OPERATOR_GRAD);

        // 2. Computing cell jacobians, inversed jacobians and jacobian determinants to get cell measure.
        DynRankView jacobians("jacobians", getMeshComponents().size(), _countCubPoints, kdefault_space_dim, kdefault_space_dim);
        Kokkos::deep_copy(jacobians, 0.0);
        Intrepid2::CellTools<DeviceType>::setJacobian(jacobians, _cubPoints, _getTetrahedronVertices(), _getTetrahedronCellTopology());

        DynRankView invJacobians("invJacobians", getMeshComponents().size(), _countCubPoints, kdefault_space_dim, kdefault_space_dim);
        Kokkos::deep_copy(invJacobians, 0.0);
        Intrepid2::CellTools<DeviceType>::setJacobianInv(invJacobians, jacobians);

        DynRankView jacobiansDet("jacobiansDet", getMeshComponents().size(), _countCubPoints);
        Kokkos::deep_copy(jacobiansDet, 0.0);
        Intrepid2::CellTools<DeviceType>::setJacobianDet(jacobiansDet, jacobians);
        DynRankView cellMeasures("cellMeasures", getMeshComponents().size(), _countCubPoints);
        Kokkos::deep_copy(cellMeasures, 0.0);
        Intrepid2::FunctionSpaceTools<DeviceType>::computeCellMeasure(cellMeasures, jacobiansDet, _cubWeights);

        // 3. Transforming reference basis gradients to physical frame.
        DynRankView transformedBasisGradients("transformedBasisGradients", getMeshComponents().size(), _countBasisFunctions, _countCubPoints, kdefault_space_dim);
        Kokkos::deep_copy(transformedBasisGradients, 0.0);
        Intrepid2::FunctionSpaceTools<DeviceType>::HGRADtransformGRAD(transformedBasisGradients, invJacobians, referenceBasisGrads);

        // 4. Multiply transformed basis gradients by cell measures to get weighted gradients.
        DynRankView weightedBasisGrads("weightedBasisGrads", getMeshComponents().size(), _countBasisFunctions, _countCubPoints, kdefault_space_dim);
        Kokkos::deep_copy(weightedBasisGrads, 0.0);
        Intrepid2::FunctionSpaceTools<DeviceType>::multiplyMeasure(weightedBasisGrads, cellMeasures, transformedBasisGradients);

        // 5. Integrate to get local stiffness matrices for workset cells.
        DynRankView localStiffnessMatrices("localStiffnessMatrices", getMeshComponents().size(), _countBasisFunctions, _countBasisFunctions);
        Kokkos::deep_copy(localStiffnessMatrices, 0.0);
        Intrepid2::FunctionSpaceTools<DeviceType>::integrate(localStiffnessMatrices, weightedBasisGrads, transformedBasisGradients);

        // Filling map with basis grads on each node on each tetrahedron.
        for (size_t localTetraId{}; localTetraId < getMeshComponents().size(); ++localTetraId)
        {
            auto globalTetraId{getMeshComponents().getMeshComponents().at(localTetraId).globalTetraId};
            for (short localNodeId{}; localNodeId < _countBasisFunctions; ++localNodeId)
            {
                auto globalNodeId{getMeshComponents().getMeshComponents().at(localTetraId).nodes.at(localNodeId).globalNodeId};
                Point grad(weightedBasisGrads(localTetraId, localNodeId, 0, 0),
                           weightedBasisGrads(localTetraId, localNodeId, 0, 1),
                           weightedBasisGrads(localTetraId, localNodeId, 0, 2));

                // As we have polynom order = 1, that all the values from the ∇φ in all cub points are the same, so we can add only 1 row from each ∇φ.
                getMeshComponents().assignNablaPhi(globalTetraId, globalNodeId, grad);
            }
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

std::vector<GSMatrixAssemblier::MatrixEntry> GSMatrixAssemblier::_getMatrixEntries()
{
    TetrahedronIndicesVector globalNodeIndicesPerElement;
    std::set<size_t> allNodeIDs;
    for (auto const &tetrahedronData : getMeshComponents().getMeshComponents())
        for (auto const &nodeData : tetrahedronData.nodes)
            allNodeIDs.insert(nodeData.globalNodeId);
    for (auto const &tetrahedronData : getMeshComponents().getMeshComponents())
    {
        std::array<LocalOrdinal, 4ul> nodes;
        for (short i{}; i < kdefault_tetrahedron_vertices_count; ++i)
            nodes[i] = tetrahedronData.nodes[i].globalNodeId - 1;
        globalNodeIndicesPerElement.emplace_back(nodes);
    }

    // 1. Getting all LSMs.
    auto localStiffnessMatrices{_computeLocalStiffnessMatrices()};

    // 3. Filling matrix entries.
    std::vector<GSMatrixAssemblier::MatrixEntry> matrixEntries;
    try
    {
        for (size_t tetraId{}; tetraId < globalNodeIndicesPerElement.size(); ++tetraId)
        {
            auto const &nodeIndices{globalNodeIndicesPerElement.at(tetraId)};
            for (size_t localNodeI{}; localNodeI < kdefault_tetrahedron_vertices_count; ++localNodeI)
            {
                for (size_t localNodeJ{}; localNodeJ < kdefault_tetrahedron_vertices_count; ++localNodeJ)
                {
                    Scalar value{localStiffnessMatrices(tetraId, localNodeI, localNodeJ)};
                    GlobalOrdinal globalRow{nodeIndices[localNodeI]},
                        globalCol{nodeIndices[localNodeJ]};

                    matrixEntries.push_back({globalRow, globalCol, value});
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
        values[i] = (indices[i] == nodeID) ? value : 0.0; // Set diagonal value to the value = 1, other - to 0 to correctly solve matrix equation Ax=b.

    // 3. Replace the modified row back into the matrix.
    m_gsmatrix->replaceGlobalValues(nodeID, indices, values);
}

void GSMatrixAssemblier::_assembleGlobalStiffnessMatrix()
{
    try
    {
        // 1. Getting all matrix entries.
        auto matrixEntries{_getMatrixEntries()};

        // 2. Getting unique global entries.
        std::map<GlobalOrdinal, std::set<GlobalOrdinal>> graphEntries;
        for (auto const &entry : matrixEntries)
            graphEntries[entry.row].insert(entry.col);

        // 3. Initializing all necessary variables.
        short indexBase{};
        auto countGlobalNodes{graphEntries.size()};

        // 4. Initializing tpetra map.
        m_map = Teuchos::rcp(new MapType(countGlobalNodes, indexBase, m_comm));

        // 5. Initializing tpetra graph.
        std::vector<size_t> numEntriesPerRow(countGlobalNodes);
        for (auto const &rowEntry : graphEntries)
            numEntriesPerRow.at(m_map->getLocalElement(rowEntry.first)) = rowEntry.second.size();

        Teuchos::RCP<Tpetra::CrsGraph<>> graph{Teuchos::rcp(new Tpetra::CrsGraph<>(m_map, Teuchos::ArrayView<size_t const>(numEntriesPerRow.data(), numEntriesPerRow.size())))};
        for (auto const &rowEntries : graphEntries)
        {
            std::vector<GlobalOrdinal> columns(rowEntries.second.begin(), rowEntries.second.end());
            Teuchos::ArrayView<GlobalOrdinal const> colsView(columns.data(), columns.size());
            graph->insertGlobalIndices(rowEntries.first, colsView);
        }
        graph->fillComplete();

        // 6. Initializing GSM.
        m_gsmatrix = Teuchos::rcp(new TpetraMatrixType(graph));

        // 7. Adding local stiffness matrices to the global.
        for (auto const &entry : matrixEntries)
        {
            Teuchos::ArrayView<GlobalOrdinal const> colsView(std::addressof(entry.col), 1);
            Teuchos::ArrayView<Scalar const> valsView(std::addressof(entry.value), 1);
            m_gsmatrix->sumIntoGlobalValues(entry.row, colsView, valsView);
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

GSMatrixAssemblier::GSMatrixAssemblier(std::string_view mesh_filename, short desiredCalculationAccuracy)
    : m_mesh_filename(mesh_filename.data()), m_comm(Tpetra::getDefaultComm()), m_desiredAccuracy(desiredCalculationAccuracy)
{
    if (desiredCalculationAccuracy <= 0)
        throw std::runtime_error("Desired calculation accuracy can't be negative or equals to 0");

    _initializeCubature();
    _assembleGlobalStiffnessMatrix();
}

bool GSMatrixAssemblier::empty() const { return m_gsmatrix->getGlobalNumEntries() == 0; }

void GSMatrixAssemblier::setBoundaryConditions(std::map<GlobalOrdinal, Scalar> const &boundaryConditions)
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
        for (auto const &[nodeInGmsh, value] : boundaryConditions)
        {
            for (int j{}; j < kdefault_polynom_order; ++j)
            {
                GlobalOrdinal nodeID{(nodeInGmsh - 1) * kdefault_polynom_order + j};

                if (nodeID >= static_cast<GlobalOrdinal>(rows()))
                    throw std::runtime_error(util::stringify("Boundary condition refers to node index ",
                                                             nodeID,
                                                             ", which exceeds the maximum row index of ",
                                                             rows() - 1, "."));

                _setBoundaryConditionForNode(nodeID, 1); // Maybe there is need to be 1, to have value = `value` in `x` vector, while solve Ax=b.
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
