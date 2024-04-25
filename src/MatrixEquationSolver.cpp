#include "../include/FiniteElementMethod/MatrixEquationSolver.hpp"
#include "../include/Utilities/Utilities.hpp"

void MatrixEquationSolver::initialize()
{
    m_A = m_assemblier.getGlobalStiffnessMatrix();
    m_x = Teuchos::rcp(new TpetraVectorType(m_A->getRowMap()));
    m_rhs = m_solutionVector.getSolutionVector();
    m_x->putScalar(0.0); // Initialize solution vector `x` with zeros.
}

MatrixEquationSolver::MatrixEquationSolver(GSMatrixAssemblier const &assemblier, SolutionVector const &solutionVector)
    : m_assemblier(assemblier), m_solutionVector(solutionVector) { initialize(); }

void MatrixEquationSolver::setRHS(const Teuchos::RCP<TpetraVectorType> &rhs) { m_rhs = rhs; }

Scalar MatrixEquationSolver::getScalarFieldValueFromX(size_t nodeID) const
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    // 1. Calculating initial index for `nodeID` node.
    short polynomOrder{m_assemblier.getPolynomOrder()};
    size_t actualIndex{nodeID * polynomOrder};
    if (actualIndex >= m_x->getLocalLength())
        throw std::runtime_error(util::stringify("Node index ", actualIndex, " is out of range in the solution vector."));

    Teuchos::ArrayRCP<Scalar const> data{m_x->getData(0)};
    Scalar value{};

    // 2. Accumulating values for all DOFs.
    if (polynomOrder == 1)
        value = data[actualIndex];
    if (polynomOrder > 1)
    {
        for (int i{}; i < polynomOrder; ++i)
            value += data[actualIndex + i];
        value /= polynomOrder;
    }

    return value;
}

std::vector<Scalar> MatrixEquationSolver::getValuesFromX() const
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    Teuchos::ArrayRCP<Scalar const> data{m_x->getData(0)};
    return std::vector<Scalar>(data.begin(), data.end());
}

void MatrixEquationSolver::writeResultsToPosFile() const
{
    if (m_x.is_null())
    {
        WARNINGMSG("There is nothing to show. Solution vector is empty.");
        return;
    }

    try
    {
        std::ofstream posFile("scalarField.pos");
        posFile << "View \"Scalar Field\" {\n";
        auto nodes{m_assemblier.getNodes()};
        for (auto const &[nodeID, coords] : nodes)
        {
            double value{getScalarFieldValueFromX(nodeID - 1)};
            posFile << std::format("SP({}, {}, {}){{{}}};\n", coords[0], coords[1], coords[2], value);
        }
        posFile << "};\n";
        posFile.close();
        LOGMSG("File 'scalarField.pos' was successfully created");
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while writing results to the .pos file");
    }
}

bool MatrixEquationSolver::solve()
{
    try
    {
        auto problem{Teuchos::rcp(new Belos::LinearProblem<Scalar, TpetraMultiVector, TpetraOperator>())};
        problem->setOperator(m_A);
        problem->setLHS(m_x);
        problem->setRHS(m_rhs);

        if (!problem->setProblem())
            return false;

        Belos::SolverFactory<Scalar, TpetraMultiVector, TpetraOperator> factory;
        auto solver{factory.create("CG", Teuchos::parameterList())};
        solver->setProblem(problem);

        Belos::ReturnType result{solver->solve()};
        return (result == Belos::Converged);
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Solver: Unknown error was occured while trying to solve equation");
    }
    return false;
}

void MatrixEquationSolver::solveAndPrint()
{
    try
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
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Solver: Unknown error occured");
    }
}

void MatrixEquationSolver::printRHS() const { m_solutionVector.print(); }

void MatrixEquationSolver::printLHS() const
{
    auto x{SolutionVector(m_solutionVector.size())};
    x.setSolutionVector(m_x);
    x.print();
}
