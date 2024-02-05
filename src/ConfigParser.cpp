#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "../include/Geometry/Mesh.hpp"
#include "../include/Utilities/ConfigParser.hpp"

void ConfigParser::clearConfig()
{
    m_config.particles_count = 0ul;
    m_config.num_threads = 0u;
    m_config.time_step = 0.0;
    m_config.simtime = 0.0;
    m_config.temperature = 0.0;
    m_config.pressure = 0.0;
    m_config.volume = 0.0;
    m_config.energy = 0.0;
    m_config.projective = Unknown;
    m_config.gas = Unknown;
    m_config.mshfilename.clear();
    m_config.model.clear();

    m_isValid = false;
}

double ConfigParser::getConfigData(std::string_view config)
{
    if (config.empty())
        return EMPTY_STR;

    std::ifstream ifs(config.data());
    if (ifs.bad())
        return BAD_FILE;

    std::string line;
    while (std::getline(ifs, line))
    {
        std::istringstream iss(line);
        std::string key;
        if (std::getline(iss, key, ':'))
        {
            std::string value;
            std::getline(iss, value);

            if (key == "Count")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.particles_count))
                    return BAD_PARTICLE_COUNT;
            }
            else if (key == "Threads")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.num_threads))
                    return BAD_THREAD_COUNT;
            }
            else if (key == "Time Step")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.time_step))
                    return BAD_TIME_STEP;
            }
            else if (key == "Simulation Time")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.simtime))
                    return BAD_SIMTIME;
            }
            else if (key == "T")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.temperature))
                    return BAD_TEMPERATURE;
            }
            else if (key == "P")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.pressure))
                    return BAD_PRESSURE;
            }
            else if (key == "V")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.volume))
                {
                    // Stripping first whitespace
                    m_config.mshfilename = value.substr(1ul);
                    m_config.volume = Mesh::getVolumeFromMesh(m_config.mshfilename);
                }
            }
            else if (key == "Particles")
            {
                size_t whitespace_pos{value.find_last_of(' ')};
                if (whitespace_pos == std::string::npos)
                    return BAD_PARTICLES_FORMAT;

                // Starting from 1 because 0 is whitespace
                m_config.projective = util::getParticleTypeFromStrRepresentation(value.substr(1ul, whitespace_pos - 1ul));
                m_config.gas = util::getParticleTypeFromStrRepresentation(value.substr(whitespace_pos + 1ul));
            }
            else if (key == "Energy")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> m_config.energy))
                    return BAD_ENERGY;
            }
            else if (key == "Model")
            {
                m_config.model = value.substr(1ul);
            }
        }
    }

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
    if (m_config.pressure <= 0.0)
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
    auto res{getConfigData(config)};
    if (res != STATUS_OK)
        std::cerr << "Error occured! Code: " << STATUS_TO_STR(res) << '\n';
}

ConfigParser::~ConfigParser() { clearConfig(); }
