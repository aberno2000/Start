#ifndef GSMatrixAssemblier_HPP
#define GSMatrixAssemblier_HPP

#include "../Geometry/Mesh.hpp"
#include "TrilinosTypes.hpp"

class GSMatrixAssemblier final
{
private:
    std::string_view m_meshfilename;                              ///< GMSH mesh file.
    Commutator m_comm;                                            ///< Handles inter-process communication within a parallel computing environment. MPI communicator.
    Teuchos::RCP<MapType> m_map;                                  ///< A smart pointer managing the lifetime of a Map object, which defines the layout of distributed data across the processes in a parallel computation.
    short m_polynomOrder{}, m_desiredAccuracy{};                  ///< Polynom order and desired accuracy of calculations.
    short _countCubPoints{}, _countBasisFunctions{}, _spaceDim{}; ///< Private data members to store count of cubature points/cubature weights and count of basis functions.
    size_t _countTetrahedra{};                                    ///< Private data member - count of tetrahedra in specified mesh.
    DynRankView _cubPoints, _cubWeights;                          ///< Storing cubature points and cubature weights in static data members because theay are initialized in ctor.
    Teuchos::RCP<TpetraMatrixType> m_gsmatrix;                    ///< Smart pointer on the global stiffness matrix.

    struct MatrixEntry
    {
        GlobalOrdinal row; ///< Global row index for the matrix entry.
        GlobalOrdinal col; ///< Global column index for the matrix entry.
        Scalar value;      ///< Value to be inserted at (row, col) in the global matrix.
    };

    /// @brief Returns tetrahedron cell topology.
    shards::CellTopology _getTetrahedronCellTopology() const;

    /**
     * @brief Retrieves a basis object for tetrahedral elements using a specified polynomial order.
     * @details This function creates a basis using hierarchical high-order polynomials on tetrahedral elements.
     *          The basis type is HGRAD (hierarchical gradient), which is suitable for representing solutions
     *          of scalar field problems such as temperature or pressure distribution.
     * @return An Intrepid2 basis object configured for the specified polynomial order.
     */
    auto _getBasis() const;

    /**
     * @brief Constructs a cubature (numerical integration) factory for tetrahedral elements with specified accuracy.
     * @details This function initializes a cubature factory capable of creating cubature rules that
     *          are accurate to a specified polynomial degree. The cubature integrates polynomial
     *          functions exactly up to the specified degree and is essential for accurately computing
     *          integrals over tetrahedral finite elements.
     * @return A cubature object created using the default cubature factory, capable of integrating up to the specified accuracy.
     */
    auto _getCubatureFactory();

    /// @brief Initializes cubature points and weights according to the mesh and polynomial order.
    void _initializeCubature();

    /**
     * @brief Retrieves the vertices of a tetrahedron from given mesh parameters.
     * @param meshParams The parameters defining the mesh.
     * @return Dynamically ranked view of the vertices in the mesh.
     */
    DynRankView _getTetrahedronVertices(MeshTetrahedronParamVector const &meshParams) const;

    /**
     * @brief Computes the tetrahedron basis function values for a given mesh parameter.
     * @param meshParam The mesh parameter containing the geometry of a tetrahedron.
     * @return Tetrahedron basis function values matrix.
     */
    DynRankView _computeTetrahedronBasisFunctionValues();

    /**
     * @brief Computes the tetrahedron transformed to physical frame basis function values for a given mesh parameter.
     * @param meshParam The mesh parameter containing the geometry of a tetrahedron.
     * @return Tetrahedron basis function values matrix, that are transformed to physical frame.
     */
    DynRankView _computeTetrahedronBasisFunctionValuesTransformed(MeshTetrahedronParamVector const &meshParams);

    /**
     * @brief Computes the tetrahedron basis function gradients for a given mesh parameter.
     * @param meshParams The mesh parameter containing the geometry of a tetrahedron.
     * @return Tetrahedron basis function gradients matrix.
     */
    DynRankView _computeTetrahedronBasisFunctionGradients();

    /**
     * @brief Computes the gradients of the tetrahedron basis functions transformed to the physical frame for a given mesh parameter.
     * @details This function calculates the gradients of basis functions in the reference coordinate system and transforms them to the physical coordinate system based on the mesh parameters. This transformation is crucial for finite element calculations in the physical domain.
     * @param meshParams The mesh parameter containing the geometry of a tetrahedron.
     * @return Dynamically ranked view of the transformed basis function gradients.
     */
    DynRankView _computeTetrahedronBasisFunctionGradientsTransformed(MeshTetrahedronParamVector const &meshParams);

    /**
     * @brief Computes the Jacobians for cells based on mesh parameters.
     * @details Jacobians are calculated for transforming integral calculations from the reference element to the physical element. This is critical for accurate finite element integration over the actual geometry represented by the mesh.
     * @param meshParams The mesh parameters defining the geometry of each cell.
     * @return Dynamically ranked view of the Jacobians for each cell.
     */
    DynRankView _computeCellJacobians(MeshTetrahedronParamVector const &meshParams);

    /**
     * @brief Computes the inverse of the Jacobians for a set of cells.
     * @details The inverse Jacobians are used for transforming gradients of basis functions from the physical domain back to the reference domain, which is essential for correct assembly of stiffness matrices.
     * @param jacobians The Jacobians for which the inverses are to be computed.
     * @return Dynamically ranked view of the inverse Jacobians.
     */
    DynRankView _computeInverseJacobians(DynRankView const &jacobians);

    /**
     * @brief Computes the local stiffness matrix for a given set of basis gradients and cubature weights.
     * @param basisGradients The gradients of the basis functions.
     * @return The local stiffness matrix.
     */
    DynRankView _computeLocalStiffnessMatrices(DynRankView const &basisGradients) const;

    /**
     * @brief Retrieves matrix entries from calculated local stiffness matrices.
     * @param basisGradients Gradients of basis functions for stiffness calculations.
     * @param globalNodeIndicesPerElement Global indices of nodes per element.
     * @return A vector of matrix entries, each containing global row, column, and value.
     */
    std::vector<GSMatrixAssemblier::MatrixEntry> _getMatrixEntries(DynRankView const &basisGradients,
                                                                   TetrahedronIndicesVector const &globalNodeIndicesPerElement);

    /**
     * @brief Assembles the global stiffness matrix using local stiffness matrices.
     * @param basisGradients Gradients of basis functions used in the assembly.
     * @param globalNodeIndicesPerElement Global indices of nodes per element.
     * @return Smart pointer to the assembled global stiffness matrix.
     */
    void _assemblyGlobalStiffnessMatrixHelper(DynRankView const &basisGradients,
                                              TetrahedronIndicesVector const &globalNodeIndicesPerElement);

public:
    GSMatrixAssemblier(std::string_view mesh_filename, int polynomOrder = 1, int desiredCalculationAccuracy = 1);
    ~GSMatrixAssemblier() {}

    /**
     * @brief Assemlies global stiffness matrix from the GMSH mesh file (.msh).
     * @param mesh_filename Mesh filename.
     * @return Sparse matrix: global stiffness matrix of the tetrahedron mesh.
     */
    void assembleGlobalStiffnessMatrix(std::string_view mesh_filename);

    /* === Getters for matrix params. === */
    constexpr Teuchos::RCP<TpetraMatrixType> const &getGlobalStiffnessMatrix() const { return m_gsmatrix; }
    size_t rows() const { return m_gsmatrix->getGlobalNumRows(); }
    size_t cols() const { return m_gsmatrix->getGlobalNumCols(); }
    Scalar getScalarFieldValue(GlobalOrdinal nodeID) const;

    /// @brief Checks is the global stiffness matrix empty or not.
    bool empty() const;

    /**
     * @brief Getter for value from global stiffness matrix.
     * @param row Row in the sparse global stiffness matrix.
     * @param col Column in the sparse global stiffness matrix.
     * @return Value from [i][j] specified row and column.
     */
    Scalar getValueFromGSM(GlobalOrdinal row, GlobalOrdinal col) const;

    /**
     * @brief Sets the boundary conditions to the global stiffness matrix. Changes specified values from map.
     * @param boundaryConditions Map for the boundary conditions. Key - ID of diagonal element (row and col). Value - value to be assigned.
     */
    void setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions);

    /// @brief Prints the entries of a Tpetra CRS matrix.
    void print() const;
};

#endif // !GSMatrixAssemblier_HPP
