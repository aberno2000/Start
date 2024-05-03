#ifndef MATRIX_EQUATION_SOLVER_HPP
#define MATRIX_EQUATION_SOLVER_HPP

#include "GSMatrixAssemblier.hpp"
#include "SolutionVector.hpp"
#include "TrilinosTypes.hpp"

class MatrixEquationSolver
{
private:
    GSMatrixAssemblier m_assemblier;      ///< Instance of the matrix assemblier.
    SolutionVector m_solutionVector;      ///< Instance of the solution vector.
    Teuchos::RCP<TpetraVectorType> m_rhs; ///< Right-hand side vector 'b'.
    Teuchos::RCP<TpetraVectorType> m_x;   ///< Solution vector 'x'.
    Teuchos::RCP<TpetraMatrixType> m_A;   ///< Matrix 'A'.

    /// @brief Initializes the matrix, solution, and RHS vectors
    void initialize();

public:
    /// @brief Ctor with params.
    MatrixEquationSolver(GSMatrixAssemblier const &assemblier, SolutionVector const &solutionVector);

    /// @brief Dtor.
    ~MatrixEquationSolver() {}

    /// @brief Sets the RHS vector 'b'.
    void setRHS(Teuchos::RCP<TpetraVectorType> const &rhs);

    /* Getters for the all components of the equation. */
    Teuchos::RCP<TpetraVectorType> getRHS() const { return m_rhs; }
    Teuchos::RCP<TpetraVectorType> getLHS() const { return m_x; }
    Teuchos::RCP<TpetraMatrixType> getGlobalStiffnessMatrix() const { return m_A; }
    Scalar getScalarFieldValueFromX(size_t nodeID) const;
    std::vector<Scalar> getValuesFromX() const;

    /**
     * @brief Forms node potential map:
     * Key   - node ID.
     * Value - electrical potential in this node.
     */
    std::map<GlobalOrdinal, Scalar> getNodePotentialMap() const;

    /**
     * @brief Calculates and returns a map of the cumulative electric field vectors for each tetrahedron.
     *
     * @details This function computes the electric field vectors in two stages:
     *          1. For each node, the electric field vector is calculated using the formula:
     *             Ei = -Σφi⋅∇φi
     *             where φi is the potential at node 'i', and ∇φi is the gradient of the basis
     *             function associated with node 'i'. This step accumulates the contributions of the
     *             potential and its gradient to the electric field at each node.
     *          2. For each tetrahedron, the cumulative electric field vector is computed by summing
     *             up the electric field vectors of all its nodes. This gives a representation of the
     *             overall electric field influence within each tetrahedron, providing insights into
     *             the combined effects of the electric fields from all constituent nodes.
     *
     *          The result is a map where each key corresponds to a tetrahedron ID, and each value
     *          is the cumulative electric field vector for that tetrahedron, representing the
     *          aggregated influence of all its nodes' electric fields.
     *
     * @return std::map<GlobalOrdinal, MathVector> A map where each key is a tetrahedron ID and
     *         each value is the corresponding cumulative electric field vector for that tetrahedron.
     *         The electric field vector components are computed as the negative sums of the products
     *         of potentials and their respective gradient vectors across all nodes within the tetrahedron.
     */
    std::map<GlobalOrdinal, MathVector> getElectricFieldMap() const;

    /// @brief Writes solution vector to the .pos file (GMSH format) to have the capability to view results of the solved equation Ax=b.
    void writeElectricPotentialsToPosFile() const;

    /// @brief Writes solution vector to the .pos file (GMSH format) to have the capability to view results of the solved equation Ax=b.
    void writeElectricFieldVectorsToPosFile() const;

    /// @brief Solves the equation Ax=b.
    bool solve();

    /// @brief Solves the equation Ax=b and prints results to the terminal.
    void solveAndPrint();

    /// @brief Prints the vectors to the terminal.
    void printLHS() const;
    void printRHS() const;
};

#endif // !MATRIX_EQUATION_SOLVER_HPP
