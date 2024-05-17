#include <chrono>
#include <nlohmann/json.hpp>
#include <sstream>
#include <sys/stat.h>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Utilities/ConfigParser.hpp"
#include "../include/Utilities/Utilities.hpp"

using json = nlohmann::json;

std::string util::getCurTime(std::string_view format)
{
    std::chrono::system_clock::time_point tp{std::chrono::system_clock::now()};
    time_t tt{std::chrono::system_clock::to_time_t(tp)};
    tm *t{localtime(&tt)};
    std::stringstream ss;
    ss << std::put_time(t, std::string(format).c_str());
    return ss.str();
}

std::string util::getStatusName(int status)
{
    switch (status)
    {
    case -15:
        return "BAD_MSHFILE";
    case -14:
        return "JSON_BAD_PARSE";
    case -13:
        return "JSON_BAD_PARAM";
    case -12:
        return "BAD_PARTICLE_COUNT";
    case -11:
        return "BAD_THREAD_COUNT";
    case -10:
        return "BAD_TIME_STEP";
    case -9:
        return "BAD_SIMTIME";
    case -8:
        return "BAD_VOLUME";
    case -7:
        return "BAD_PRESSURE";
    case -6:
        return "BAD_TEMPERATURE";
    case -5:
        return "BAD_ENERGY";
    case -4:
        return "BAD_MODEL";
    case -3:
        return "UNKNOWN_PARTICLES";
    case -2:
        return "BAD_PARTICLES_FORMAT";
    case -1:
        return "BAD_FILE";
    case 0:
        return "EMPTY_STR";
    case 1:
        return "STATUS_OK";
    default:
        return "UNKNOWN_ERROR";
    }
}

ParticleType util::getParticleTypeFromStrRepresentation(std::string_view particle)
{
    if (particle == "Ar")
        return Ar;
    else if (particle == "Ne")
        return Ne;
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

std::string util::getParticleType(ParticleType ptype)
{
    switch (ptype)
    {
    case Ar:
        return "Ar";
    case Ne:
        return "Ne";
    case He:
        return "He";
    case Ti:
        return "Ti";
    case Al:
        return "Al";
    case Sn:
        return "Sn";
    case W:
        return "W";
    case Au:
        return "Au";
    case Ni:
        return "Ni";
    case Ag:
        return "Ag";
    default:
        return "Unknown";
    }
}

double util::calculateConcentration(std::string_view config)
{
    ConfigParser parser(config);
    if (parser.isInvalid())
        return -1.0;

    // n = PV/RT * N_Avogadro
    return parser.getPressure() * parser.getVolume() * constants::physical_constants::N_av /
           (parser.getTemperature() * constants::physical_constants::R);
}

bool util::exists(std::string_view filename)
{
#ifdef __unix__
    struct stat buf;
    return (stat(filename.data(), std::addressof(buf)) == 0);
#endif
#ifdef _WIN32
    struct _stat buf;
    return (_stat(filename.data(), std::addressof(buf)) == 0);
#endif
}

void util::checkRestrictions(double time_step, size_t particles_count, std::string_view mshfilename)
{
    if (not util::exists(mshfilename))
    {
        ERRMSG(util::stringify("File (", mshfilename, ") doesn't exist"));
        std::exit(EXIT_FAILURE);
    }
    if (time_step <= 0.0)
    {
        ERRMSG(util::stringify("Time step can't be less or equal 0"));
        std::exit(EXIT_FAILURE);
    }
    if (particles_count > 10'000'000)
    {
        ERRMSG(util::stringify("Particles count limited by 10'000'000.\nBut you entered ", particles_count));
        std::exit(EXIT_FAILURE);
    }
}

std::array<double, 6> util::getParticleSourceCoordsAndDirection()
{
    std::string path("sourceAndDirection.txt");
    std::ifstream ifs(path);
    if (!ifs.is_open())
    {
        ERRMSG("Can't read coordinates of the particle source");
        std::exit(EXIT_FAILURE);
    }

    std::array<double, 6> result;
    for (short i{}; i < 6; ++i)
    {
        if (!(ifs >> result[i]))
        {
            if (i != 3)
                ERRMSG("Failed to read coordinate #" + std::to_string(i + 1) + " from the particle source");
            if (i == 3)
                ERRMSG("Failed to read expansion angle θ");
            if (i == 4)
                ERRMSG("Failed to read angle φ");
            if (i == 5)
                ERRMSG("Failed to read angle θ");

            ifs.close();                   // Ensure the file is closed before exiting.
            std::filesystem::remove(path); // Remove the file for clean-up.
            std::exit(EXIT_FAILURE);
        }
    }

    ifs.close();
    std::filesystem::remove(path); // Remove the file after successful reading

    return result;
}

util::BoundaryConditionsData util::loadBoundaryConditions(std::string_view filename)
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

    std::vector<std::pair<std::vector<size_t>, double>> boundaryConditions;
    std::vector<size_t> nonChangebleNodes;
    json j;

    try
    {
        file >> j;
    }
    catch (const json::parse_error &e)
    {
        throw std::runtime_error("Failed to parse JSON file: " + std::string(filename) + ". Error: " + e.what());
    }

    for (auto const &[key, value] : j.items())
    {
        std::vector<size_t> nodes;
        std::string nodesStr = key;
        size_t pos{};
        std::string token;
        while ((pos = nodesStr.find(',')) != std::string::npos)
        {
            token = nodesStr.substr(0ul, pos);
            try
            {
                nodes.emplace_back(std::stoi(token));
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
                nonChangebleNodes.emplace_back(nodeId);
            }
            catch (const std::invalid_argument &e)
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

        boundaryConditions.emplace_back(nodes, val);
    }

    return std::make_pair(nonChangebleNodes, boundaryConditions);
}
