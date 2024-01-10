#ifndef SETTINGS_HPP
#define SETTINGS_HPP

#include <concepts>
#include <filesystem>
#include <source_location>
#include <sstream>
#include <string_view>

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

namespace settings
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
    constexpr std::string stringify(Args &&...args)
    {
        std::ostringstream oss;
        (oss << ... << args);
        return oss.str();
    }

    namespace physical_constants
    {
        static constinit const double R{8.314};              // [J/k*mol]
        static constinit const double T{300};                // [k]
        static constinit const double N_av{6.22e23};         // Avogadro number
        static constinit const double eV_J{1.602176565e-19}; // Conversion factor of eV to 
        static constinit const double J_eV{6.242e+18};       // Conversion factor of J to eV
    }
}

#endif // !SETTINGS_HPP
