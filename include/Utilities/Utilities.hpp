#ifndef UTILITIES_HPP
#define UTILITIES_HPP

/* Standard headers */
#include <concepts>
#include <filesystem>
#include <format>
#include <iostream>
#include <source_location>
#include <sstream>
#include <string_view>

/* CGAL headers */
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/intersections.h>
using Kernel = CGAL::Exact_predicates_inexact_constructions_kernel;
using Point3 = Kernel::Point_3;
using Ray3 = Kernel::Ray_3;
using Triangle3 = Kernel::Triangle_3;
using Tetrahedron3 = Kernel::Tetrahedron_3;
using MeshTetrahedronParam = std::tuple<size_t, Tetrahedron3, double>;
using MeshTetrahedronParamVector = std::vector<MeshTetrahedronParam>;

/* Trilinos headers */
#include <BelosSolverFactory.hpp>
#include <BelosTpetraAdapter.hpp>
#include <Intrepid2_CellTools.hpp>
#include <Intrepid2_DefaultCubatureFactory.hpp>
#include <Intrepid2_FunctionSpaceTools.hpp>
#include <Intrepid2_HGRAD_TET_C1_FEM.hpp>
#include <Intrepid_FunctionSpaceTools.hpp>
#include <Kokkos_Core.hpp>
#include <Panzer_DOFManager.hpp>
#include <Panzer_IntrepidFieldPattern.hpp>
#include <Shards_CellTopology.hpp>
#include <Teuchos_GlobalMPISession.hpp>
#include <Teuchos_ParameterList.hpp>
#include <Teuchos_RCP.hpp>
#include <Tpetra_BlockCrsMatrix_Helpers_def.hpp>
#include <Tpetra_BlockCrsMatrix_decl.hpp>
#include <Tpetra_Core.hpp>
#include <Tpetra_CrsMatrix.hpp>
#include <Tpetra_CrsMatrix_decl.hpp>
#include <Tpetra_Map.hpp>
#include <Tpetra_Vector.hpp>
#include <eigen3/Eigen/Sparse>
using ExecutionSpace = Kokkos::DefaultExecutionSpace;                 // Using host space to interoperate with data.
using DeviceType = Kokkos::Device<ExecutionSpace, Kokkos::HostSpace>; // Using CPU.
using SpMat = Eigen::SparseMatrix<double>;                            // Eigen sparse matrix type.
using Scalar = double;                                                // ST - Scalar Type (type of the data inside the matrix node).
using LocalOrdinal = int;                                             // LO (indeces in local matrix).
using GlobalOrdinal = long long;                                      // GO - Global Ordinal Type (indeces in global matrices).
using Node = Tpetra::Map<>::node_type;                                // Node type based on Kokkos execution space.
using MapType = Tpetra::Map<LocalOrdinal, GlobalOrdinal, Node>;
using TpetraVectorType = Tpetra::Vector<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraMultiVector = Tpetra::MultiVector<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraOperator = Tpetra::Operator<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraMatrixType = Tpetra::CrsMatrix<Scalar, LocalOrdinal, GlobalOrdinal, Node>;

#include "Constants.hpp"
using namespace constants;
using namespace particle_types;

#define JSON_BAD_PARSE -14.0
#define JSON_BAD_PARAM -13.0
#define BAD_MSHFILE -15.0
#define BAD_PARTICLE_COUNT -12.0
#define BAD_THREAD_COUNT -11.0
#define BAD_TIME_STEP -10.0
#define BAD_SIMTIME -9.0
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

#ifdef __linux__
#define COMMON_PRETTY_FUNC __PRETTY_FUNCTION__
#endif
#ifdef _WIN32
#define COMMON_PRETTY_FUNC __FUNCSIG__
#endif

#define CGAL_TO_DOUBLE(var) CGAL::to_double(var)
#define ERRMSG_ABS_PATH(desc) std::cerr << std::format("\033[1;31mError:\033[0m\033[1m {}: {}({} line): {}: \033[1;31m{}\033[0m\033[1m\n", \
                                                       util::getCurTime(),                                                                 \
                                                       std::source_location::current().file_name(),                                        \
                                                       std::source_location::current().line(),                                             \
                                                       COMMON_PRETTY_FUNC, desc);
#define LOGMSG_ABS_PATH(desc) std::clog << std::format("Log: {}: {}({} line): {}: {}\n",            \
                                                       util::getCurTime(),                          \
                                                       std::source_location::current().file_name(), \
                                                       std::source_location::current().line(),      \
                                                       COMMON_PRETTY_FUNC, desc);
#define EXTRACT_FILE_NAME(filepath) std::filesystem::path(std::string(filepath).c_str()).filename().string()
#define ERRMSG(desc) std::cerr << std::format("\033[1;31mError:\033[0m\033[1m {}: {}({} line): {}: \033[1;31m{}\033[0m\033[1m\n", \
                                              util::getCurTime(),                                                                 \
                                              EXTRACT_FILE_NAME(std::source_location::current().file_name()),                     \
                                              std::source_location::current().line(),                                             \
                                              COMMON_PRETTY_FUNC, desc);
#define LOGMSG(desc) std::clog << std::format("Log: {}: {}({} line): {}: {}\n",                               \
                                              util::getCurTime(),                                             \
                                              EXTRACT_FILE_NAME(std::source_location::current().file_name()), \
                                              std::source_location::current().line(),                         \
                                              COMMON_PRETTY_FUNC, desc);
#define WARNINGMSG(desc) std::cerr << std::format("\033[1;33mWarning:\033[0m\033[1m {}: {}({} line): {}: {}\n",   \
                                                  util::getCurTime(),                                             \
                                                  EXTRACT_FILE_NAME(std::source_location::current().file_name()), \
                                                  std::source_location::current().line(),                         \
                                                  COMMON_PRETTY_FUNC, desc);

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
        (oss << ... << std::forward<Args>(args));
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

    /**
     * @brief Checker for file on existence.
     * @param filaname Name of the file (or path) to check it.
     * @return `true` if file exists, otherwise `false`.
     */
    bool exists(std::string_view filename);

    /**
     * @brief Calculates the volume of a tetrahedron.
     * @details This function computes the volume of a tetrahedron by utilizing the CGAL library. The volume is calculated
     *          based on the determinant of a matrix constructed from the coordinates of the tetrahedron's vertices. The formula
     *          for the volume of a tetrahedron given its vertices A, B, C, and D is |dot(AB, cross(AC, AD))| / 6.
     * @param tetrahedron The tetrahedron whose volume is to be calculated.
     * @return The volume of the tetrahedron.
     */
    double calculateVolumeOfTetrahedron3(Tetrahedron3 const &tetrahedron);

    /**
     * @brief Prints the contents of a Kokkos matrix.
     * @param matrix The matrix to print.
     */
    void printMatrix(const Kokkos::DynRankView<double, DeviceType> &matrix);

    /**
     * @brief Computes the tetrahedron basis functions for a given mesh parameter.
     * @param meshParam The mesh parameter containing the geometry of a tetrahedron.
     * @return A pair containing a vector of basis functions values and a DynRankView of cubature weights.
     */
    std::pair<std::vector<Kokkos::DynRankView<double, DeviceType>>, Kokkos::DynRankView<double, DeviceType>>
    computeTetrahedronBasisFunctions(MeshTetrahedronParam const &meshParam);

    /**
     * @brief Computes the local stiffness matrix for a given set of basis gradients and cubature weights.
     * @param basisGradients The gradients of the basis functions.
     * @param cubWeights The cubature weights.
     * @return The local stiffness matrix.
     */
    Kokkos::DynRankView<double, DeviceType> computeLocalStiffnessMatrix(
        std::vector<Kokkos::DynRankView<double, DeviceType>> const &basisGradients,
        Kokkos::DynRankView<double, DeviceType> const &cubWeights);

    /**
     * @brief Assembles the global stiffness matrix from local stiffness matrices.
     * @param meshParams The mesh parameters for the entire domain.
     * @param allBasisGradients The gradients of the basis functions for each element.
     * @param allCubWeights The cubature weights for each element.
     * @param totalNodes The total number of nodes in the mesh.
     * @param globalNodeIndicesPerElement The global node indices for each element.
     * @return The global stiffness matrix in Eigen's sparse matrix format.
     */
    SpMat assembleGlobalStiffnessMatrix(
        MeshTetrahedronParamVector const &meshParams,
        std::vector<std::vector<Kokkos::DynRankView<double, DeviceType>>> const &allBasisGradients,
        std::vector<Kokkos::DynRankView<double, DeviceType>> const &allCubWeights,
        int totalNodes,
        std::vector<std::array<int, 4>> const &globalNodeIndicesPerElement);

    /**
     * @brief Fills a vector with random numbers within a specified range.
     * @param b The vector to fill.
     * @param size The size of the vector.
     * @param lower The lower bound of the random numbers (default=-100.0).
     * @param upper The upper bound of the random numbers (default=100.0).
     */
    void fillVectorWithRandomNumbers(Eigen::VectorXd &b, int size, double lower = -100.0, double upper = 100.0);

    /**
     * @brief Converts an Eigen sparse matrix to a Tpetra CRS matrix.
     * @param eigenMatrix The Eigen sparse matrix to convert.
     * @return The converted Tpetra CRS matrix.
     */
    TpetraMatrixType convertEigenToTpetra(SpMat const &eigenMatrix);

    /**
     * @brief Prints the entries of a Tpetra CRS matrix.
     * @param matrix The matrix whose entries are to be printed.
     */
    void printLocalMatrixEntries(TpetraMatrixType const &matrix);

    /**
     * @brief Prints the contents of a Tpetra vector.
     * @param vec The vector to print.
     */
    void printTpetraVector(TpetraVectorType const &vec);
}

#endif // !UTILITIES_HPP
