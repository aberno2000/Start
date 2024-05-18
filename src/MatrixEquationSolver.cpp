#include <nlohmann/json.hpp>
using json = nlohmann::json;

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

std::map<GlobalOrdinal, Scalar> MatrixEquationSolver::getNodePotentialMap() const
{
    if (m_x.is_null())
        throw std::runtime_error("Solution vector is not initialized");

    std::map<GlobalOrdinal, Scalar> nodePotentialMap;
    GlobalOrdinal id{1};
    for (Scalar potential : getValuesFromX())
        nodePotentialMap[id++] = potential;
    return nodePotentialMap;
}

std::map<GlobalOrdinal, MathVector> MatrixEquationSolver::calculateElectricFieldMap() const
{
    try
    {
        std::map<GlobalOrdinal, MathVector> electricFieldMap;
        auto basisFuncGradientsMap{m_assemblier.getBasisFuncGradsMap()};
        if (basisFuncGradientsMap.empty())
        {
            WARNINGMSG("There is no basis function gradients");
            return electricFieldMap;
        }

        auto nodePotentialsMap{getNodePotentialMap()};
        if (nodePotentialsMap.empty())
        {
            WARNINGMSG("There are no potentials in nodes. Maybe you forget to calculate the matrix equation Ax=b");
            return electricFieldMap;
        }

        auto tetraVolumesMap{m_assemblier.getTetrahedraVolumesMap()};
        if (tetraVolumesMap.empty())
        {
            WARNINGMSG("Storage for the tetrahedron volumes is empty for some reason. It might lead to unexpected results");
            return electricFieldMap;
        }

        // We have map: (Tetrahedron ID | map<Node ID | Basis function gradient math vector (3 components)>).
        // To get electric field of the cell we just need to accumulate all the basis func grads for each node for each tetrahedron:
        // E_cell = -1/(6V)*Σ(φi⋅∇φi), where i - global index of the node.
        for (const auto &[tetraId, nodeGradientMap] : basisFuncGradientsMap)
        {
            MathVector electricField{};
            double volumeFactor{1.0 / (6.0 * tetraVolumesMap.at(tetraId))};

            // Accumulate the electric field contributions from each node
            for (const auto &[nodeId, gradient] : nodeGradientMap)
            {
                if (nodePotentialsMap.find(nodeId) != nodePotentialsMap.end())
                {
                    double potentialInNode{nodePotentialsMap.at(nodeId)};
                    electricField += gradient * potentialInNode;
                }
                else
                    WARNINGMSG("Node ID not found in potentials map");
            }
            electricField *= -volumeFactor;
            electricFieldMap[tetraId] = electricField;
        }

        if (electricFieldMap.empty())
            WARNINGMSG("Something went wrong: There is no electric field in the mesh")
        return electricFieldMap;
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while writing results to the .pos file");
    }
    WARNINGMSG("Returning empty electric field map");
    return std::map<GlobalOrdinal, MathVector>();
}

void MatrixEquationSolver::writeElectricPotentialsToPosFile() const
{
    if (m_x.is_null())
    {
        WARNINGMSG("There is nothing to show. Solution vector is empty.");
        return;
    }

    try
    {
        std::ofstream posFile("electricPotential.pos");
        posFile << "View \"Scalar Field\" {\n";
        auto nodes{m_assemblier.getNodes()};
        for (auto const &[nodeID, coords] : nodes)
        {
            double value{getScalarFieldValueFromX(nodeID - 1)};
            posFile << std::format("SP({}, {}, {}){{{}}};\n", coords[0], coords[1], coords[2], value);
        }
        posFile << "};\n";
        posFile.close();
        LOGMSG("File 'electricPotential.pos' was successfully created");
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

void MatrixEquationSolver::writeElectricFieldVectorsToPosFile() const
{
    if (m_x.is_null())
    {
        WARNINGMSG("There is nothing to show. Solution vector is empty.");
        return;
    }

    auto tetrahedronCentres{m_assemblier.getTetrahedronCentres()};
    if (tetrahedronCentres.empty())
    {
        WARNINGMSG("There is nothing to show. Storage for the tetrahedron centres is empty.");
        return;
    }

    auto electricFieldMap{calculateElectricFieldMap()};
    if (electricFieldMap.empty())
    {
        WARNINGMSG("There is nothing to show. Storage for the electric field values is empty.");
        return;
    }

    try
    {
        std::ofstream posFile("electricField.pos");
        posFile << "View \"Vector Field\" {\n";
        for (auto const &[tetraId, fieldVector] : electricFieldMap)
        {
            auto x{tetrahedronCentres.at(tetraId).at(0)},
                y{tetrahedronCentres.at(tetraId).at(1)},
                z{tetrahedronCentres.at(tetraId).at(2)};

            posFile << std::format("VP({}, {}, {}){{{}, {}, {}}};\n",
                                   x, y, z,
                                   fieldVector.getX(), fieldVector.getY(), fieldVector.getZ());
        }

        posFile << "};\n";
        posFile.close();
        LOGMSG("File 'electricField.pos' was successfully created");
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
        params->set("Solver Name", solverName);
        params->set("Maximum Iterations", maxIterations);
        params->set("Convergence Tolerance", convergenceTolerance);
        params->set("Verbosity", verbosity);
        params->set("Output Frequency", outputFrequency);

        if (solverName == "GMRES" || solverName == "Block GMRES" || solverName == "Pseudo-block GMRES" || solverName == "Block Flexible GMRES")
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
        else if (solverName == "CG" || solverName == "Block CG" || solverName == "Pseudo-block CG")
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
        else if (solverName == "GCRO-DR")
        {
            params->set("Num Blocks", numBlocks);
            params->set("Block Size", blockSize);
            params->set("Maximum Restarts", maxRestarts);
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
            params->set("Number of Blocks", std::stoi(j.at("numBlocks").get<std::string>()));
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
    std::filesystem::remove(filename);
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

void MatrixEquationSolver::printRHS() const { m_solutionVector.print(); }

void MatrixEquationSolver::printLHS() const
{
    auto x{SolutionVector(m_solutionVector.size())};
    x.setSolutionVector(m_x);
    x.print();
}
