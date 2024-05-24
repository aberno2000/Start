#ifndef GSMatrixAssemblier_HPP
#define GSMatrixAssemblier_HPP

/* ATTENTION: Works well only for the polynom order = 1. */

#include "../DataHandling/VolumetricMeshData.hpp"
#include "../Geometry/Mesh.hpp"
#include "TrilinosTypes.hpp"

/// @brief This class works only with `VolumetricMeshData` singleton object.
class GSMatrixAssemblier final
{
private:
    static constexpr short const kdefault_polynom_order{1};
    static constexpr short const kdefault_tetrahedron_vertices_count{4};
    static constexpr short const kdefault_space_dim{3};

    std::string m_mesh_filename; ///< Filename of the mesh.

    Commutator m_comm;                         ///< Handles inter-process communication within a parallel computing environment. MPI communicator.
    Teuchos::RCP<MapType> m_map;               ///< A smart pointer managing the lifetime of a Map object, which defines the layout of distributed data across the processes in a parallel computation.
    Teuchos::RCP<TpetraMatrixType> m_gsmatrix; ///< Smart pointer on the global stiffness matrix.

    short m_desiredAccuracy{};                       ///< Polynom order and desired accuracy of calculations.
    short _countCubPoints{}, _countBasisFunctions{}; ///< Private data members to store count of cubature points/cubature weights and count of basis functions.
    DynRankView _cubPoints, _cubWeights;             ///< Storing cubature points and cubature weights in static data members because theay are initialized in ctor.

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

    /// @brief Initializes cubature points and weights according to the mesh and polynomial order.
    void _initializeCubature();

    /**
     * @brief Retrieves the vertices of all tetrahedrons in the mesh.
     *
     * This function extracts the coordinates of the vertices for each tetrahedron
     * in the mesh and stores them in a multi-dimensional array (DynRankView).
     * The dimensions of the array are [number of tetrahedrons] x [4 vertices] x [3 coordinates (x, y, z)].
     *
     * @return DynRankView A multi-dimensional array containing the vertices of all tetrahedrons.
     *                     Each tetrahedron is represented by its four vertices, and each vertex has three coordinates (x, y, z).
     * @throw std::runtime_error if an error occurs during the extraction of vertices.
     */
    DynRankView _getTetrahedronVertices();

    /**
     * @brief Computes the local stiffness matrix for a given set of basis gradients and cubature weights.
     * @return The local stiffness matrix.
     */
    DynRankView _computeLocalStiffnessMatrices();

    /**
     * @brief Retrieves matrix entries from calculated local stiffness matrices.
     * @return A vector of matrix entries, each containing global row, column, and value.
     */
    std::vector<GSMatrixAssemblier::MatrixEntry> _getMatrixEntries();

    /**
     * @brief Sets boundary conditions for the node with specified node ID.
     * @details Sets diagonal element to the specified value, other elements in the row sets to 0.
     * @param nodeID Node ID (row|col).
     * @param value Value to assign.
     */
    void _setBoundaryConditionForNode(LocalOrdinal nodeID, Scalar value);

    /**
     * @brief Assemlies global stiffness matrix from the GMSH mesh file (.msh).
     * @return Sparse matrix: global stiffness matrix of the tetrahedron mesh.
     */
    void _assembleGlobalStiffnessMatrix();

public:
    GSMatrixAssemblier(std::string_view mesh_filename, short desiredCalculationAccuracy);
    ~GSMatrixAssemblier() {}

    /* === Getters for matrix params. === */
    constexpr Teuchos::RCP<TpetraMatrixType> const &getGlobalStiffnessMatrix() const { return m_gsmatrix; }
    size_t rows() const { return m_gsmatrix->getGlobalNumRows(); }
    size_t cols() const { return m_gsmatrix->getGlobalNumCols(); }
    auto &getMeshComponents() { return VolumetricMeshData::getInstance(m_mesh_filename.data()); }
    auto const &getMeshComponents() const { return VolumetricMeshData::getInstance(m_mesh_filename.data()); }

    /// @brief Checks is the global stiffness matrix empty or not.
    bool empty() const;

    /**
     * @brief Sets the boundary conditions to the global stiffness matrix. Changes specified values from map.
     * @param boundaryConditions Map for the boundary conditions. Key - ID of diagonal element (row and col). Value - value to be assigned.
     */
    void setBoundaryConditions(std::map<GlobalOrdinal, Scalar> const &boundaryConditions);

    /// @brief Prints the entries of a Tpetra CRS matrix.
    void print() const;
};

#endif // !GSMatrixAssemblier_HPP
