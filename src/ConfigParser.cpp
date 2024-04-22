#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>

#include "../include/Geometry/Mesh.hpp"
#include "../include/Utilities/ConfigParser.hpp"

using json = nlohmann::json;

void ConfigParser::clearConfig()
{
    m_config = config_data_t{};
    m_isValid = false;
}

int ConfigParser::getConfigData(std::string_view config)
{
    if (config.empty())
        return EMPTY_STR;

    std::ifstream ifs(config.data());
    if (ifs.bad())
        return BAD_FILE;

    json configJson;
    try
    {
        ifs >> configJson;
    }
    catch (json::exception const &e)
    {
        std::cerr << "Error parsing config JSON: " << e.what() << std::endl;
        return JSON_BAD_PARSE;
    }

    try
    {
        m_config.mshfilename = configJson.at("Mesh File").get<std::string>();
        m_config.particles_count = configJson.at("Count").get<size_t>();
        m_config.num_threads = configJson.at("Threads").get<unsigned int>();
        m_config.time_step = configJson.at("Time Step").get<double>();
        m_config.simtime = configJson.at("Simulation Time").get<double>();
        m_config.temperature = configJson.at("T").get<double>();
        m_config.pressure = configJson.at("P").get<double>();
        m_config.volume = configJson.at("V").get<double>();

        // String that needs special handling
        std::string projective(configJson.at("Particles").at(0)),
            gas(configJson.at("Particles").at(1));
        m_config.projective = util::getParticleTypeFromStrRepresentation(projective);
        m_config.gas = util::getParticleTypeFromStrRepresentation(gas);

        m_config.energy = configJson.at("Energy").get<double>();
        m_config.model = configJson.at("Model").get<std::string>();
    }
    catch (json::exception const &e)
    {
        std::cerr << "Error parsing config JSON: " << e.what() << std::endl;
        return JSON_BAD_PARAM;
    }
    catch (std::exception const &e)
    {
        std::cerr << "General error: " << e.what() << std::endl;
        return JSON_BAD_PARAM;
    }
    catch (...)
    {
        std::cerr << "Smth wrong when assign data from the config\n";
        return EXIT_FAILURE;
    }

    m_isValid = true;

    if (m_config.mshfilename.empty() || !util::exists(m_config.mshfilename))
        return BAD_MSHFILE;
    if (m_config.particles_count == 0ul)
        return BAD_PARTICLE_COUNT;
    if (m_config.num_threads == 0)
        return BAD_THREAD_COUNT;
    if (m_config.time_step == 0)
        return BAD_TIME_STEP;
    if (m_config.simtime == 0)
        return BAD_SIMTIME;
    if (m_config.temperature <= 0.0)
        return BAD_TEMPERATURE;
    if (m_config.pressure < 0.0)
        return BAD_PRESSURE;
    if (m_config.volume <= 0.0)
        return BAD_VOLUME;
    if (m_config.projective == Unknown || m_config.gas == Unknown)
        return UNKNOWN_PARTICLES;
    if (m_config.projective < 3 || m_config.gas > 2)
        return BAD_PARTICLES_FORMAT;
    if (m_config.energy <= 0.0)
        return BAD_ENERGY;
    if (m_config.model != "HS" && m_config.model != "VHS" && m_config.model != "VSS")
        return BAD_MODEL;

    m_isValid = true;

    ifs.close();
    return STATUS_OK;
}

ConfigParser::ConfigParser(std::string_view config)
{
    m_status_code = getConfigData(config);
    if (m_status_code != STATUS_OK)
        std::cerr << "Error occured! Code: " << STATUS_TO_STR(m_status_code) << '\n';
}

ConfigParser::~ConfigParser() { clearConfig(); }
