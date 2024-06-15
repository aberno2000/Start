#include <nlohmann/json.hpp>
using json = nlohmann::json;

#include "../include/FiniteElementMethod/MatrixEquationSolver.hpp"
#include "../include/Utilities/Utilities.hpp"

void MatrixEquationSolver::initialize()
{
    m_A = m_assemblier->getGlobalStiffnessMatrix();
    m_x = Teuchos::rcp(new TpetraVectorType(m_A->getRowMap()));
    m_rhs = m_solutionVector->getSolutionVector();
    m_x->putScalar(0.0); // Initialize solution vector `x` with zeros.
}

MatrixEquationSolver::MatrixEquationSolver(std::shared_ptr<GSMatrixAssemblier> assemblier, std::shared_ptr<SolutionVector> solutionVector)
    : m_assemblier(assemblier), m_solutionVector(solutionVector) { initialize(); }

void MatrixEquationSolver::setRHS(const Teuchos::RCP<TpetraVectorType> &rhs) { m_rhs = rhs; }

Scalar MatrixEquationSolver::getScalarFieldValueFromX(size_t nodeID) const
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    // 1. Calculating initial index for `nodeID` node.
    if (nodeID >= m_x->getLocalLength())
        throw std::runtime_error(util::stringify("Node index ", nodeID, " is out of range in the solution vector."));

    Teuchos::ArrayRCP<Scalar const> data{m_x->getData(0)};
    return data[nodeID];
}

std::vector<Scalar> MatrixEquationSolver::getValuesFromX() const
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    Teuchos::ArrayRCP<Scalar const> data{m_x->getData(0)};
    return std::vector<Scalar>(data.begin(), data.end());
}

void MatrixEquationSolver::fillNodesPotential()
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    GlobalOrdinal id{1};
    for (Scalar potential : getValuesFromX())
        m_assemblier->getMeshComponents().assignPotential(id++, potential);
}

void MatrixEquationSolver::calculateElectricField()
{
    try
    {
        // Filling node potentials before calculating the electric field in the cell.
        fillNodesPotential();

        // We have map: (Tetrahedron ID | map<Node ID | Basis function gradient math vector (3 components)>).
        // To get electric field of the cell we just need to accumulate all the basis func grads for each node for each tetrahedron:
        // E_cell = -1/(6V)*Σ(φi⋅∇φi), where i - global index of the node.
        for (auto const &tetrahedronData : m_assemblier->getMeshComponents().getMeshComponents())
        {
            MathVector electricField{};
            double volumeFactor{1.0 / (6.0 * tetrahedronData.tetrahedron.volume())};

            for (auto const &node : tetrahedronData.nodes)
            {
                if (node.potential && node.nablaPhi)
                    electricField += MathVector(node.nablaPhi.value().x(), node.nablaPhi.value().y(), node.nablaPhi.value().z()) *
                                     node.potential.value();
                else
                    WARNINGMSG(util::stringify("Node potential or nablaPhi is not set for the ",
                                               node.globalNodeId, " vertex of the ", tetrahedronData.globalTetraId, " tetrahedron"));
            }
            electricField *= volumeFactor;
            m_assemblier->getMeshComponents().assignElectricField(tetrahedronData.globalTetraId, Point(electricField.getX(), electricField.getY(), electricField.getZ()));
        }
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

void MatrixEquationSolver::writeElectricPotentialsToPosFile(double time)
{
    if (m_x.is_null())
    {
        WARNINGMSG("There is nothing to show. Solution vector is empty.");
        return;
    }

    try
    {
        std::string filepath;
        filepath = (time == -1) ? "electricPotential.pos" : std::format("electricPotential_time_{}.pos", time);
        std::ofstream posFile(filepath);

        posFile << "View \"Scalar Field\" {\n";
        for (auto const &entry : m_assemblier->getMeshComponents().getMeshComponents())
        {
            for (short i{}; i < 4; ++i)
            {
                if (!entry.nodes.at(i).potential.has_value())
                {
                    WARNINGMSG(util::stringify("Electic potential for the tetrahedron ", entry.globalTetraId,
                                               " and node ", entry.nodes.at(i).globalNodeId, " is empty"));
                    continue;
                }

                auto node{entry.nodes.at(i)};
                auto globalNodeId{entry.nodes.at(i).globalNodeId};

                double value{getScalarFieldValueFromX(globalNodeId - 1)};
                posFile << std::format("SP({}, {}, {}){{{}}};\n", node.nodeCoords.x(), node.nodeCoords.y(), node.nodeCoords.z(), value);
            }
        }
        posFile << "};\n";
        posFile.close();

        LOGMSG(util::stringify("File \'", filepath, "\' was successfully created"));
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

void MatrixEquationSolver::writeElectricFieldVectorsToPosFile(double time)
{
    if (m_x.is_null())
    {
        WARNINGMSG("There is nothing to show. Solution vector is empty.");
        return;
    }

    try
    {
        std::string filepath;
        filepath = (time == -1) ? "electricField.pos" : std::format("electricField_time_{}.pos", time);
        std::ofstream posFile(filepath);

        posFile << "View \"Vector Field\" {\n";
        for (auto const &entry : m_assemblier->getMeshComponents().getMeshComponents())
        {
            if (!entry.electricField.has_value())
            {
                WARNINGMSG(util::stringify("Electic field for the tetrahedron ", entry.globalTetraId, " is empty"));
                continue;
            }

            auto x{entry.getTetrahedronCenter().x()},
                y{entry.getTetrahedronCenter().y()},
                z{entry.getTetrahedronCenter().z()};

            auto fieldVector{entry.electricField.value()};
            posFile << std::format("VP({}, {}, {}){{{}, {}, {}}};\n",
                                   x, y, z,
                                   fieldVector.x(), fieldVector.y(), fieldVector.z());
        }

        posFile << "};\n";
        posFile.close();

        LOGMSG(util::stringify("File \'", filepath, "\' was successfully created"));
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

Teuchos::RCP<Teuchos::ParameterList> MatrixEquationSolver::createSolverParams(std::string_view solverName, int maxIterations,
                                                                              double convergenceTolerance, int verbosity, int outputFrequency, int numBlocks,
                                                                              int blockSize, int maxRestarts, bool flexibleGMRES, std::string_view orthogonalization,
                                                                              bool adaptiveBlockSize, int convergenceTestFrequency)
{
    Teuchos::RCP<Teuchos::ParameterList> params{Teuchos::parameterList()};
    try
    {
        params->set("Maximum Iterations", maxIterations);
        params->set("Convergence Tolerance", convergenceTolerance);
        params->set("Verbosity", verbosity);
        params->set("Output Frequency", outputFrequency);

        if (solverName == "GMRES" || solverName == "Block GMRES")
        {
            params->set("Num Blocks", numBlocks);
            params->set("Block Size", blockSize);
            params->set("Maximum Restarts", maxRestarts);
            params->set("Flexible GMRES", flexibleGMRES);
            params->set("Orthogonalization", orthogonalization.data());
            params->set("Adaptive Block Size", adaptiveBlockSize);
            if (convergenceTestFrequency >= 0)
                params->set("Convergence Test Frequency", convergenceTestFrequency);
        }
        else if (solverName == "CG" || solverName == "Block CG")
        {
            params->set("Block Size", blockSize);
            params->set("Convergence Tolerance", convergenceTolerance);
            params->set("Maximum Iterations", maxIterations);
        }
        else if (solverName == "LSQR")
        {
            params->set("Convergence Tolerance", convergenceTolerance);
            params->set("Maximum Iterations", maxIterations);
        }
        else if (solverName == "MINRES")
        {
            params->set("Convergence Tolerance", convergenceTolerance);
            params->set("Maximum Iterations", maxIterations);
        }
        else
            throw std::invalid_argument(util::stringify("Unsupported solver name: ", solverName));
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error occurred while setting parameters for the solver.");
    }
    return params;
}

std::pair<std::string, Teuchos::RCP<Teuchos::ParameterList>> MatrixEquationSolver::parseSolverParamsFromJson(std::string_view filename)
{
    if (!std::filesystem::exists(filename))
    {
        throw std::runtime_error("File does not exist: " + std::string(filename));
    }

    if (std::filesystem::path(filename).extension() != ".json")
    {
        throw std::runtime_error("File is not a JSON file: " + std::string(filename));
    }

    std::ifstream file(filename.data());
    if (!file.is_open())
    {
        throw std::runtime_error("Unable to open file: " + std::string(filename));
    }

    json j;
    try
    {
        file >> j;
    }
    catch (json::parse_error const &e)
    {
        throw std::runtime_error("Failed to parse JSON file: " + std::string(filename) + ". Error: " + e.what());
    }

    Teuchos::RCP<Teuchos::ParameterList> params{Teuchos::rcp(new Teuchos::ParameterList())};
    std::string solverName;

    try
    {
        if (j.contains("solverName"))
            solverName = j.at("solverName").get<std::string>();
        if (j.contains("maxIterations"))
            params->set("Maximum Iterations", std::stoi(j.at("maxIterations").get<std::string>()));
        if (j.contains("convergenceTolerance"))
            params->set("Convergence Tolerance", std::stod(j.at("convergenceTolerance").get<std::string>()));
        if (j.contains("verbosity"))
            params->set("Verbosity", std::stoi(j.at("verbosity").get<std::string>()));
        if (j.contains("outputFrequency"))
            params->set("Output Frequency", std::stoi(j.at("outputFrequency").get<std::string>()));
        if (j.contains("numBlocks"))
            params->set("Num Blocks", std::stoi(j.at("numBlocks").get<std::string>()));
        if (j.contains("blockSize"))
            params->set("Block Size", std::stoi(j.at("blockSize").get<std::string>()));
        if (j.contains("maxRestarts"))
            params->set("Maximum Restarts", std::stoi(j.at("maxRestarts").get<std::string>()));
        if (j.contains("flexibleGMRES"))
            params->set("Flexible GMRES", j.at("flexibleGMRES").get<std::string>() == "true");
        if (j.contains("orthogonalization"))
            params->set("Orthogonalization", j.at("orthogonalization").get<std::string>());
        if (j.contains("adaptiveBlockSize"))
            params->set("Adaptive Block Size", j.at("adaptiveBlockSize").get<std::string>() == "true");
        if (j.contains("convergenceTestFrequency"))
            params->set("Convergence Test Frequency", std::stoi(j.at("convergenceTestFrequency").get<std::string>()));
    }
    catch (json::type_error const &e)
    {
        throw std::runtime_error("Type error in JSON file: " + std::string(filename) + ". Error: " + e.what());
    }
    return std::make_pair(solverName, params);
}

bool MatrixEquationSolver::solve(std::string_view solverName, Teuchos::RCP<Teuchos::ParameterList> solverParams)
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
        auto solver{factory.create(solverName.data(), solverParams)};
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

void MatrixEquationSolver::solveDefaultAndPrint()
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

void MatrixEquationSolver::printRHS() const { m_solutionVector->print(); }

void MatrixEquationSolver::printLHS() const
{
    auto x{SolutionVector(m_solutionVector->size())};
    x.setSolutionVector(m_x);
    x.print();
}
