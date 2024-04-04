#ifndef GSMatrixAssemblier_HPP
#define GSMatrixAssemblier_HPP

#include "../Geometry/Mesh.hpp"
#include "TrilinosTypes.hpp"

class GSMatrixAssemblier final
{
private:
    std::string_view m_meshfilename;           ///< GMSH mesh file.
    Commutator m_comm;                         ///< Handles inter-process communication within a parallel computing environment. MPI communicator.
    Teuchos::RCP<MapType> m_map;               ///< A smart pointer managing the lifetime of a Map object, which defines the layout of distributed data across the processes in a parallel computation.
    Teuchos::RCP<TpetraMatrixType> m_gsmatrix; ///< Smart pointer on the global stiffness matrix.

    /**
     * @brief Computes the tetrahedron basis functions for a given mesh parameter.
     * @param meshParam The mesh parameter containing the geometry of a tetrahedron.
     * @return A pair containing a vector of basis functions values and a DynRankView of cubature weights.
     */
    BasisFuncValues_CubatureWeights computeTetrahedronBasisFunctions(MeshTetrahedronParam const &meshParam) const;

    /**
     * @brief Computes the local stiffness matrix for a given set of basis gradients and cubature weights.
     * @param basisGradients The gradients of the basis functions.
     * @param cubWeights The cubature weights.
     * @return The local stiffness matrix.
     */
    DynRankView computeLocalStiffnessMatrix(DynRankViewVector const &basisGradients, DynRankView const &cubWeights) const;

    /**
     * @brief Assembles the global stiffness matrix from local stiffness matrices.
     * @param meshParams The mesh parameters for the entire domain.
     * @param allBasisGradients The gradients of the basis functions for each element.
     * @param allCubWeights The cubature weights for each element.
     * @param totalNodes The total number of nodes in the mesh.
     * @param globalNodeIndicesPerElement The global node indices for each element.
     * @return The global stiffness matrix in Eigen's sparse matrix format.
     */
    EigenSparseMatrix assembleGlobalStiffnessMatrixHelper(
        MeshTetrahedronParamVector const &meshParams,
        DynRankViewMatrix const &allBasisGradients,
        DynRankViewVector const &allCubWeights,
        GlobalOrdinal totalNodes,
        TetrahedronIndicesVector const &globalNodeIndicesPerElement) const;

    /**
     * @brief Converts an Eigen sparse matrix to a Tpetra CRS matrix.
     * @param sparseMatrix The Eigen sparse matrix to convert.
     * @return The converted Tpetra CRS matrix.
     */
    Teuchos::RCP<TpetraMatrixType> convertEigenToTpetra(EigenSparseMatrix const &sparseMatrix) const;

public:
    GSMatrixAssemblier(std::string_view mesh_filename);
    ~GSMatrixAssemblier() {}

    /**
     * @brief Prints the contents of a Kokkos matrix.
     * @param view The matrix to print.
     */
    void printDynRankView(DynRankView const &view) const;

    /// @brief Prints the entries of a Tpetra CRS matrix.
    void print() const;

    /**
     * @brief Assemlies global stiffness matrix from the GMSH mesh file (.msh).
     * @param mesh_filename Mesh filename.
     * @return Sparse matrix: global stiffness matrix of the tetrahedron mesh.
     */
    Teuchos::RCP<TpetraMatrixType> assembleGlobalStiffnessMatrix(std::string_view mesh_filename);

    /* === Getters for matrix params. === */
    constexpr Teuchos::RCP<TpetraMatrixType> const &getGlobalStiffnessMatrix() const { return m_gsmatrix; }
    size_t rows() const { return m_gsmatrix->getGlobalNumRows(); }
    size_t cols() const { return m_gsmatrix->getGlobalNumCols(); }
    Scalar getScalarFieldValue(GlobalOrdinal nodeID) const;

    /**
     * @brief Sets the boundary conditions to the global stiffness matrix. Changes specified values from map.
     * @param boundaryConditions Map for the boundary conditions. Key - ID of diagonal element (row and col). Value - value to be assigned.
     */
    void setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions);
};

#endif // !GSMatrixAssemblier_HPP
