#ifndef UTILITIES_HPP
#define UTILITIES_HPP

#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>

#include <concepts>
#include <filesystem>
#include <source_location>
#include <sstream>
#include <string_view>

#include "Constants.hpp"

using namespace constants;
using namespace particle_types;

using Kernel = CGAL::Exact_predicates_exact_constructions_kernel;
using Point3 = Kernel::Point_3;
using Ray3 = Kernel::Ray_3;
using Triangle3 = Kernel::Triangle_3;
using Tetrahedron3 = Kernel::Tetrahedron_3;

#define BAD_VOLUME -8.0
#define BAD_PRESSURE -7.0
#define BAD_TEMPERATURE -6.0
#define BAD_ENERGY -5.0
#define BAD_MODEL -4.0
#define UNKNOWN_PARTICLES -3.0
#define BAD_PARTICLES_FORMAT -2.0
#define BAD_FILE -1.0
#define EMPTY_STR 0.0
#define STATUS_OK 1.0

#define STATUS_TO_STR(status) util::getStatusName(status)

#define CGAL_TO_DOUBLE(var) CGAL::to_double(var)
#define ERRMSG_ABS_PATH(desc) std::cerr << std::format("\033[1;31mERROR:\033[0m\033[1m {}: {}({} line): {}: \033[1;31m{}\033[0m\033[1m\n", \
                                                       settings::getCurTime(),                                                             \
                                                       std::source_location::current().file_name(),                                        \
                                                       std::source_location::current().line(),                                             \
                                                       __PRETTY_FUNCTION__, desc);
#define LOGMSG_ABS_PATH(desc) std::clog << std::format("LOG: {}: {}({} line): {}: {}\n",            \
                                                       settings::getCurTime(),                      \
                                                       std::source_location::current().file_name(), \
                                                       std::source_location::current().line(),      \
                                                       __PRETTY_FUNCTION__, desc);
#define EXTRACT_FILE_NAME(filepath) std::filesystem::path(std::string(filepath).c_str()).filename().string()
#define ERRMSG(desc) std::cerr << std::format("\033[1;31mERROR:\033[0m\033[1m {}: {}({} line): {}: \033[1;31m{}\033[0m\033[1m\n", \
                                              settings::getCurTime(),                                                             \
                                              EXTRACT_FILE_NAME(std::source_location::current().file_name()),                     \
                                              std::source_location::current().line(),                                             \
                                              __PRETTY_FUNCTION__, desc);
#define LOGMSG(desc) std::clog << std::format("LOG: {}: {}({} line): {}: {}\n",                               \
                                              settings::getCurTime(),                                         \
                                              EXTRACT_FILE_NAME(std::source_location::current().file_name()), \
                                              std::source_location::current().line(),                         \
                                              __PRETTY_FUNCTION__, desc);

namespace util
{
    /**
     * @brief Concept that specifies all types that can be convert to "std::string_view" type
     * For example, "char", "const char *", "std::string", etc.
     * @tparam T The type to check for convertibility to std::string_view.
     */
    template <typename T>
    concept StringConvertible = std::is_convertible_v<T, std::string_view>;

    /**
     * @brief Concept that checks if variable has output operator
     * @tparam a variable to check
     * @param os output stream
     */
    template <typename T>
    concept Printable = requires(T a, std::ostream &os) {
        {
            os << a
        } -> std::same_as<std::ostream &>;
    };

    /**
     * @brief Gets the current system time in the specified format.
     * @tparam Format A format string compatible with std::put_time.
     * Defaults to "%H:%M:%S" if not specified.
     * For example, "%Y-%m-%d %H:%M:%S" for date and time in YYYY-MM-DD HH:MM:SS format.
     * @param format The format string compatible with std::put_time. Defaults to "%H:%M:%S".
     */
    std::string getCurTime(std::string_view format = "%H:%M:%S");

    /**
     * @brief Generates string with specified multiple args
     * @tparam args arguments of type that can be convert to string
     * @return String composed from all arguments
     */
    template <Printable... Args>
    std::string stringify(Args &&...args)
    {
        std::ostringstream oss;
        (oss << ... << args);
        return oss.str();
    }

    /**
     * @brief Calculates sign.
     * @details Takes a double (`val`) and returns:
     *          - -1 if `val` is less than 0,
     *          -  1 if `val` is greater than 0,
     *          -  0 if `val` is equal to 0.
     */
    constexpr double signFunc(double val)
    {
        if (val < 0)
            return -1;
        if (0 < val)
            return 1;
        return 0;
    }

    /// @brief Helper function to get status name from its value.
    std::string getStatusName(double status);

    /// @brief Helper function to parse and define particle type by string.
    ParticleType getParticleTypeFromStrRepresentation(std::string_view particle);

    /// @brief Helper function to recieve string representation of the particle type.
    std::string getParticleType(ParticleType ptype);

    /**
     * @brief Calculating concentration from the configuration file.
     * @param config Name of the configuration file.
     * @return Concentration. [N] (count).
     * `-1` if smth went wrong.
     */
    double calculateConcentration(std::string_view config);
}

#endif // !UTILITIES_HPP
