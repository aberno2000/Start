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

public:
    /// @brief Ctor with params.
    MatrixEquationSolver(GSMatrixAssemblier const &assemblier, SolutionVector const &solutionVector);
    
    /// @brief Dtor.
    ~MatrixEquationSolver() {}

    /// @brief Initializes the matrix, solution, and RHS vectors
    void initialize();

    /// @brief Sets the RHS vector 'b'.
    void setRHS(Teuchos::RCP<TpetraVectorType> const &rhs);

    /* Getters for the all components of the equation. */
    Teuchos::RCP<TpetraVectorType> getRHS() const { return m_rhs; }
    Teuchos::RCP<TpetraVectorType> getLHS() const { return m_x; }
    Teuchos::RCP<TpetraMatrixType> getGlobalStiffnessMatrix() const { return m_A; }
    Scalar getScalarFieldValueFromX(size_t nodeID) const;

    /// @brief Solves the equation Ax=b.
    bool solve();

    /// @brief Solves the equation Ax=b and prints results to the terminal.
    void solveAndPrint();

    /// @brief Prints the vectors to the terminal.
    void printLHS() const;
    void printRHS() const;
};

#endif // !MATRIX_EQUATION_SOLVER_HPP
