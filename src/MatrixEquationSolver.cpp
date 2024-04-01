#include "../include/Utilities/MatrixEquationSolver.hpp"
#include "../include/Utilities/Utilities.hpp"

MatrixEquationSolver::MatrixEquationSolver(GSMatrixAssemblier const &assemblier, SolutionVector const &solutionVector)
    : m_assemblier(assemblier), m_solutionVector(solutionVector) { initialize(); }

void MatrixEquationSolver::initialize()
{
    m_A = m_assemblier.getGlobalStiffnessMatrix();
    m_x = Teuchos::rcp(new TpetraVectorType(m_A->getRowMap()));
    m_rhs = m_solutionVector.getSolutionVector();
    m_x->putScalar(0.0); // Initialize solution vector `x` with zeros.
}

void MatrixEquationSolver::setRHS(const Teuchos::RCP<TpetraVectorType> &rhs) { m_rhs = rhs; }

bool MatrixEquationSolver::solve()
{
    auto problem{Teuchos::rcp(new Belos::LinearProblem<Scalar, TpetraMultiVector, TpetraOperator>())};
    problem->setOperator(m_A);
    problem->setLHS(m_x);
    problem->setRHS(m_rhs);

    if (!problem->setProblem())
        return false;

    Belos::SolverFactory<Scalar, TpetraMultiVector, TpetraOperator> factory;
    auto solver{factory.create("GMRES", Teuchos::parameterList())};
    solver->setProblem(problem);

    Belos::ReturnType result{solver->solve()};

    return (result == Belos::Converged);
}

void MatrixEquationSolver::solveAndPrint()
{
    auto problem{Teuchos::rcp(new Belos::LinearProblem<Scalar, TpetraMultiVector, TpetraOperator>())};
    problem->setOperator(m_A);
    problem->setLHS(m_x);
    problem->setRHS(m_rhs);

    if (!problem->setProblem())
        ERRMSG("Can't set the problem. Belos::LinearProblem::setProblem() returned an error");

    Belos::SolverFactory<Scalar, TpetraMultiVector, TpetraOperator> factory;
    auto solver{factory.create("GMRES", Teuchos::parameterList())};
    solver->setProblem(problem);

    Belos::ReturnType result{solver->solve()};

    if (result == Belos::Converged)
    {
        LOGMSG("\033[1;32mSolution converged\033[0m\033[1m");
    }
    else
    {
        ERRMSG("Solution did not converge");
    }
}

void MatrixEquationSolver::printRHS() const { m_solutionVector.print(); }

void MatrixEquationSolver::printLHS() const
{
    auto x{SolutionVector(m_solutionVector.size())};
    x.setSolutionVector(m_x);
    x.print();
}
