#include <chrono>
#include <sstream>
#include <sys/stat.h>

#include "../include/Utilities/ConfigParser.hpp"
#include "../include/Utilities/Utilities.hpp"

std::string util::getCurTime(std::string_view format)
{
    std::chrono::system_clock::time_point tp{std::chrono::system_clock::now()};
    time_t tt{std::chrono::system_clock::to_time_t(tp)};
    tm *t{localtime(&tt)};
    std::stringstream ss;
    ss << std::put_time(t, std::string(format).c_str());
    return ss.str();
}

std::string util::getStatusName(double status)
{
    switch (static_cast<int>(status))
    {
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
        return "UNKNOWN_STATUS";
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

double util::calculateVolumeOfTetrahedron3(Tetrahedron3 const &tetrahedron)
{
    Point3 const &A{tetrahedron[0]},
        &B{tetrahedron[1]},
        &C{tetrahedron[2]},
        &D{tetrahedron[3]};

    // Construct vectors AB, AC, and AD
    Kernel::Vector_3 AB{B - A}, AC{C - A}, AD{D - A};

    // Compute the scalar triple product (AB . (AC x AD))
    double scalarTripleProduct{CGAL::scalar_product(AB, CGAL::cross_product(AC, AD))};

    // The volume of the tetrahedron is the absolute value of the scalar triple product divided by 6
    return std::abs(scalarTripleProduct) / 6.0;
}
