#ifndef MATRIX_EQUATION_SOLVER_HPP
#define MATRIX_EQUATION_SOLVER_HPP

/* ATTENTION: Works well only for the polynom order = 1. */

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
     * @details The result is a map where each key corresponds to a tetrahedron ID, and each value
     *          is the cumulative electric field vector for that tetrahedron, representing the
     *          aggregated influence of all its nodes' electric fields.
     *
     * @return std::map<GlobalOrdinal, MathVector> A map where each key is a tetrahedron ID and
     *         each value is the corresponding cumulative electric field vector for that tetrahedron.
     *         The electric field vector components are computed as the negative sums of the products
     *         of potentials and their respective gradient vectors across all nodes within the tetrahedron.
     */
    std::map<GlobalOrdinal, MathVector> calculateElectricFieldMap() const;

    /// @brief Writes solution vector to the .pos file (GMSH format) to have the capability to view results of the solved equation Ax=b.
    void writeElectricPotentialsToPosFile() const;

    /// @brief Writes solution vector to the .pos file (GMSH format) to have the capability to view results of the solved equation Ax=b.
    void writeElectricFieldVectorsToPosFile() const;

    /**
     * @brief Creates and configures a parameter list for the specified iterative solver.
     *
     * This method initializes and configures a `Teuchos::ParameterList` with the specified parameters for the given iterative solver.
     * It sets default values for all parameters and handles exceptions that may occur during the parameter setting process.
     *
     * Supported iterative solvers include:
     * - "CG" (Conjugate Gradient)
     * - "Block CG"
     * - "GMRES" (Generalized Minimal Residual)
     * - "Block GMRES"
     * - "Pseudo-block GMRES"
     * - "Block Flexible GMRES"
     * - "GCRO-DR" (Generalized Conjugate Residual with Deflated Restarting)
     * - "Pseudo-block CG"
     * - "LSQR"
     * - "MINRES"
     *
     * @param solverName The name of the iterative solver (e.g., "GMRES", "CG").
     * @param maxIterations The maximum number of iterations the solver will perform (default: 1000).
     * @param convergenceTolerance The tolerance for the relative residual norm used to determine convergence (default: 1e-8).
     * @param verbosity Controls the amount and type of information printed during the solution process (default: Belos::Errors + Belos::Warnings + Belos::IterationDetails).
     * @param outputFrequency Determines how often information is printed during the iterative process (default: 1).
     * @param numBlocks Sets the number of blocks in the Krylov basis, related to the restart mechanism of GMRES (default: 30).
     * @param blockSize Determines the block size for block methods (default: 1).
     * @param maxRestarts Specifies the maximum number of restarts allowed (default: 20).
     * @param flexibleGMRES Indicates whether to use the flexible version of GMRES (default: false).
     * @param orthogonalization Specifies the orthogonalization method to use, options include "ICGS" and "IMGS" (default: "ICGS").
     * @param adaptiveBlockSize Indicates whether to adapt the block size in block methods (default: false).
     * @param convergenceTestFrequency Specifies how often convergence is tested (in iterations). If negative, the default setting is used (default: -1).
     *
     * @return A `Teuchos::RCP` to the configured `Teuchos::ParameterList`.
     */
    Teuchos::RCP<Teuchos::ParameterList> createSolverParams(
        std::string_view solverName = "GMRES",
        int maxIterations = 1000,
        double convergenceTolerance = 1e-8,
        int verbosity = Belos::Errors + Belos::Warnings + Belos::IterationDetails,
        int outputFrequency = 1,
        int numBlocks = 30,
        int blockSize = 1,
        int maxRestarts = 20,
        bool flexibleGMRES = false,
        std::string_view orthogonalization = "ICGS",
        bool adaptiveBlockSize = false,
        int convergenceTestFrequency = -1);

    /**
     * @brief Solves the equation Ax=b.
     * @details This method initializes and configures the solver, sets up the linear problem, and solves it using the specified iterative method.
     * @param solverName Name of the iterative solver.
     * @param solverParams Iterative solver parameters that you can set with method `createSolverParams`.
     * @return true if the solver converged to a solution, false otherwise.
     */
    bool solve(std::string_view solverName, Teuchos::RCP<Teuchos::ParameterList> solverParams);

    /// @brief Solves the equation Ax=b and prints results to the terminal. Solves with default params and as default uses GMRES iterative solver.
    void solveDefaultAndPrint();

    /// @brief Prints the vectors to the terminal.
    void printLHS() const;
    void printRHS() const;
};

#endif // !MATRIX_EQUATION_SOLVER_HPP
