#include <fstream>
#include <sstream>
#include <string>

#include <format>
#include <iostream>

#include "../include/Geometry/Mesh.hpp"
#include "../include/Utilities/ConcentrationCalculator.hpp"

double ConcentrationCalculator::temperature = 0.0;
double ConcentrationCalculator::pressure = 0.0;
double ConcentrationCalculator::volume = 0.0;
double ConcentrationCalculator::energy = 0.0;
ParticleType ConcentrationCalculator::projective = Al;
ParticleType ConcentrationCalculator::gas = Ar;
std::string ConcentrationCalculator::mshfilename;
std::string ConcentrationCalculator::model;

ParticleType ConcentrationCalculator::getParticleTypeFromStrRepresentation(std::string particle)
{
    if (particle == "Ar")
        return Ar;
    else if (particle == "N")
        return N;
    else if (particle == "He")
        return He;
    else if (particle == "Ti")
        return Ti;
    else if (particle == "Al")
        return Al;
    else if (particle == "Sn")
        return Sn;
    else if (particle == "W")
        return W;
    else if (particle == "Au")
        return Au;
    else if (particle == "Cu")
        return Cu;
    else if (particle == "Ni")
        return Ni;
    else if (particle == "Ag")
        return Ag;
    else
        return Unknown;
}

double ConcentrationCalculator::getParams(std::string_view config)
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

            if (key == "T")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> temperature))
                    return BAD_TEMPERATURE;
                if (temperature <= 0.0)
                    return BAD_TEMPERATURE;
            }
            else if (key == "P")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> pressure))
                    return BAD_PRESSURE;
                if (pressure <= 0.0)
                    return BAD_PRESSURE;
            }
            else if (key == "V/msh")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> volume))
                {
                    // Stripping first whitespace
                    mshfilename = value.substr(1ul);
                    volume = Mesh::getVolumeFromMesh(mshfilename);
                }
                if (volume <= 0.0)
                    return BAD_VOLUME;
            }
            else if (key == "Particles")
            {
                size_t whitespace_pos{value.find_last_of(' ')};
                if (whitespace_pos == std::string::npos)
                    return BAD_PARTICLES_FORMAT;

                // Starting from 1 because 0 is whitespace
                projective = getParticleTypeFromStrRepresentation(value.substr(1ul, whitespace_pos - 1ul));
                gas = getParticleTypeFromStrRepresentation(value.substr(whitespace_pos + 1ul));

                if (projective == Unknown || gas == Unknown)
                    return UNKNOWN_PARTICLES;
                if (projective < 3 || gas > 2)
                    return BAD_PARTICLES_FORMAT;
            }
            else if (key == "Energy")
            {
                std::istringstream tmp_iss(value);
                if (!(tmp_iss >> energy))
                    return BAD_ENERGY;
                if (energy <= 0.0)
                    return BAD_ENERGY;
            }
            else if (key == "Model")
            {
                model = value.substr(1ul);
                if (model != "HS" && model != "VHS" && model != "VSS")
                    return BAD_MODEL;
            }
        }
    }
    ifs.close();

    std::cout << std::format("T: {}\nP: {}\nV/msh: {}\nParticles: {} {}\nEnergy: {}\nModel: {}\n",
                             temperature, pressure, volume, static_cast<int>(projective),
                             static_cast<int>(gas), energy, model);

    return STATUS_OK;
}

double ConcentrationCalculator::calculateConcentration(std::string_view config)
{
    auto res{getParams(config)};
    if (res != STATUS_OK)
        return res;

    double concentration{};
    // TODO: Calculate concentration from specified conditions
    if (model == "HS")
    {
    }
    else if (model == "VHS")
    {
    }
    else if (model == "VSS")
    {
    }

    return concentration;
}
