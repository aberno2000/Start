#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>

#include "../include/Utilities/ConfigParser.hpp"

using json = nlohmann::json;
/**
 * @brief Checks if a required parameter exists in the JSON object.
 *
 * @param j The JSON object to check.
 * @param param The parameter name to check for.
 * @throw std::runtime_error if the parameter does not exist.
 */
void checkParameterExists(json const &j, std::string_view param)
{
    if (!j.contains(param.data()))
        throw std::runtime_error("Missing required parameter: " + std::string(param) + ". Example: \"" + std::string(param) + "\": <value>");
}

void ConfigParser::getConfigData(std::string_view config)
{
    if (config.empty())
        throw std::runtime_error("Configuration file path is empty.");

    std::ifstream ifs(config.data());
    if (!ifs)
        throw std::runtime_error("Failed to open configuration file: " + std::string(config));

    json configJson;
    try
    {
        ifs >> configJson;
    }
    catch (json::exception const &e)
    {
        throw std::runtime_error("Error parsing config JSON: " + std::string(e.what()));
    }

    try
    {
        // Check for all required parameters in the JSON file
        checkParameterExists(configJson, "Mesh File");
        checkParameterExists(configJson, "Count");
        checkParameterExists(configJson, "Threads");
        checkParameterExists(configJson, "Time Step");
        checkParameterExists(configJson, "Simulation Time");
        checkParameterExists(configJson, "T");
        checkParameterExists(configJson, "P");
        checkParameterExists(configJson, "Particles");
        checkParameterExists(configJson, "Energy");
        checkParameterExists(configJson, "Model");
        checkParameterExists(configJson, "EdgeSize");
        checkParameterExists(configJson, "DesiredAccuracy");

        m_config.mshfilename = configJson.at("Mesh File").get<std::string>();
        m_config.particles_count = configJson.at("Count").get<size_t>();
        m_config.num_threads = configJson.at("Threads").get<unsigned int>();
        m_config.time_step = configJson.at("Time Step").get<double>();
        m_config.simtime = configJson.at("Simulation Time").get<double>();
        m_config.temperature = configJson.at("T").get<double>();
        m_config.pressure = configJson.at("P").get<double>();

        if (configJson.at("Particles").size() < 2)
        {
            throw std::runtime_error("Parameter 'Particles' must contain at least two values. Example: \"Particles\": [\"type1\", \"type2\"]");
        }
        std::string projective{configJson.at("Particles").at(0)},
            gas{configJson.at("Particles").at(1)};

        m_config.projective = util::getParticleTypeFromStrRepresentation(projective);
        m_config.gas = util::getParticleTypeFromStrRepresentation(gas);

        m_config.energy = configJson.at("Energy").get<double>();
        m_config.model = configJson.at("Model").get<std::string>();

        if (configJson.contains("ParticleSourcePoint"))
        {
            json particleSource = configJson.at("ParticleSourcePoint");
            checkParameterExists(particleSource, "phi");
            checkParameterExists(particleSource, "theta");
            checkParameterExists(particleSource, "expansionAngle");
            checkParameterExists(particleSource, "BaseCoordinates");

            m_config.phi = particleSource.at("phi").get<double>();
            m_config.theta = particleSource.at("theta").get<double>();
            m_config.expansionAngle = particleSource.at("expansionAngle").get<double>();
            m_config.baseCoordinates = particleSource.at("BaseCoordinates").get<std::vector<double>>();
            m_config.isPointSource = true;
        }

        if (configJson.contains("ParticleSourceSurface"))
        {
            // TODO: Implement when surface source will be implemented.
        }

        m_config.edgeSize = std::stod(configJson.at("EdgeSize").get<std::string>());
        m_config.desiredAccuracy = std::stoi(configJson.at("DesiredAccuracy").get<std::string>());

        // Iterative solver parameters.
        if (configJson.contains("solverName"))
            m_config.solverName = configJson.at("solverName").get<std::string>();
        if (configJson.contains("maxIterations"))
            m_config.maxIterations = std::stoi(configJson.at("maxIterations").get<std::string>());
        if (configJson.contains("convergenceTolerance"))
            m_config.convergenceTolerance = std::stod(configJson.at("convergenceTolerance").get<std::string>());
        if (configJson.contains("verbosity"))
            m_config.verbosity = std::stoi(configJson.at("verbosity").get<std::string>());
        if (configJson.contains("outputFrequency"))
            m_config.outputFrequency = std::stoi(configJson.at("outputFrequency").get<std::string>());
        if (configJson.contains("numBlocks"))
            m_config.numBlocks = std::stoi(configJson.at("numBlocks").get<std::string>());
        if (configJson.contains("blockSize"))
            m_config.blockSize = std::stoi(configJson.at("blockSize").get<std::string>());
        if (configJson.contains("maxRestarts"))
            m_config.maxRestarts = std::stoi(configJson.at("maxRestarts").get<std::string>());
        if (configJson.contains("flexibleGMRES"))
            m_config.flexibleGMRES = configJson.at("flexibleGMRES").get<std::string>() == "true";
        if (configJson.contains("orthogonalization"))
            m_config.orthogonalization = configJson.at("orthogonalization").get<std::string>();
        if (configJson.contains("adaptiveBlockSize"))
            m_config.adaptiveBlockSize = configJson.at("adaptiveBlockSize").get<std::string>() == "true";
        if (configJson.contains("convergenceTestFrequency"))
            m_config.convergenceTestFrequency = std::stoi(configJson.at("convergenceTestFrequency").get<std::string>());

        // Boundary conditions.
        if (configJson.contains("Boundary Conditions"))
        {
            json boundaryConditionsJson = configJson.at("Boundary Conditions");
            for (auto const &[key, value] : boundaryConditionsJson.items())
            {
                std::vector<size_t> nodes;
                std::string nodesStr(key);
                size_t pos{};
                std::string token;
                while ((pos = nodesStr.find(',')) != std::string::npos)
                {
                    token = nodesStr.substr(0ul, pos);
                    try
                    {
                        size_t nodeId{std::stoul(token)};
                        nodes.emplace_back(nodeId);
                        m_config.nonChangeableNodes.emplace_back(nodeId);
                        m_config.nodeValues[nodeId].emplace_back(value.get<double>());
                    }
                    catch (std::invalid_argument const &e)
                    {
                        throw std::runtime_error("Invalid node ID: " + token + ". Error: " + e.what());
                    }
                    catch (std::out_of_range const &e)
                    {
                        throw std::runtime_error("Node ID out of range: " + token + ". Error: " + e.what());
                    }
                    nodesStr.erase(0ul, pos + 1ul);
                }
                if (!nodesStr.empty())
                {
                    try
                    {
                        size_t nodeId{std::stoul(nodesStr)};
                        nodes.emplace_back(nodeId);
                        m_config.nonChangeableNodes.emplace_back(nodeId);
                        m_config.nodeValues[nodeId].emplace_back(value.get<double>());
                    }
                    catch (std::invalid_argument const &e)
                    {
                        throw std::runtime_error("Invalid node ID: " + nodesStr + ". Error: " + e.what());
                    }
                    catch (std::out_of_range const &e)
                    {
                        throw std::runtime_error("Node ID out of range: " + nodesStr + ". Error: " + e.what());
                    }
                }

                double val{};
                try
                {
                    val = value.get<double>();
                }
                catch (json::type_error const &e)
                {
                    throw std::runtime_error("Invalid value for node IDs: " + key + ". Error: " + e.what());
                }

                m_config.boundaryConditions.emplace_back(nodes, val);
            }

            // Check for duplicate nodes.
            for (auto const &[nodeId, values] : m_config.nodeValues)
            {
                if (values.size() > 1)
                {
                    std::cerr << "Node ID " << nodeId << " has multiple values assigned: ";
                    for (double val : values)
                        std::cerr << val << ' ';
                    std::cerr << std::endl;

                    ifs.close();
                    throw std::runtime_error("Duplicate node values found. Temporary file with boundary conditions has been deleted.");
                }
            }
        }
    }
    catch (json::exception const &e)
    {
        throw std::runtime_error("Error parsing config JSON: " + std::string(e.what()));
    }
    catch (std::exception const &e)
    {
        throw std::runtime_error("General error: " + std::string(e.what()));
    }
    catch (...)
    {
        throw std::runtime_error("Something went wrong when assigning data from the config.");
    }
}
