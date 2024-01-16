#ifndef VOLUMECREATOR_HPP
#define VOLUMECREATOR_HPP

#include <aabb/AABB.h>
#include <concepts>
#include <numbers>
#include <span>
#include <tuple>
#include <vector>

#include "MathVector.hpp"
#include "Mesh.hpp"

enum VolumeType
{
    BoxType,
    SphereType,
    CylinderType,
    ConeType
};

/// @brief Interface for volume creation in GMSH.
class IVolume
{
public:
    /**
     * @brief Pure virtual function to create a geometric volume.
     * This function is a pure virtual member function declared in the base class IVolume.
     * It must be implemented in derived classes (e.g., Box, Sphere, Cylinder, Cone)
     * to create a geometric volume in the corresponding shape.
     *
     * @return An integer value indicating the status of the volume creation:
     *       - Zero or positive value typically signifies a successful creation.
     *       - Negative value or error code denotes a failure or specific error condition.
     *
     * @note This function must be overridden by derived classes to define the specific behavior
     * for creating the geometric volume of that particular type.
     */
    virtual int create() const = 0;
    virtual aabb::AABB const &getBoundingBox() const = 0;
    virtual ~IVolume() {}
};

/**
 * @brief Concept for Sphere type.
 * Requirements for a type to satisfy this concept:
 *  - Must be a tuple of size 4.
 *  - All elements must be a floating-point type.
 * This concept ensures that the provided type represents a sphere with its coordinates
 * and radius in the form of a tuple.
 */
template <typename T>
concept SphereConcept = std::tuple_size_v<T> == 2 &&
                        is_mathvector_v<std::tuple_element_t<0, T>> &&
                        std::is_floating_point_v<std::tuple_element_t<1, T>>;
using SphereT = std::tuple<PositionVector, double>;
using SphereVector = std::vector<SphereT>;
using SphereSpan = std::span<SphereT const>;

/// @brief Represents Box volume.
class Box final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{};
    aabb::AABB m_bounding_box;

public:
    explicit Box(double x_, double y_, double z_,
                 double dx_, double dy_, double dz_);
    int create() const override;
    aabb::AABB const &getBoundingBox() const override { return m_bounding_box ;}
};

/// @brief Represents Sphere volume.
class Sphere final : public IVolume
{
private:
    double x{}, y{}, z{}, r{};
    aabb::AABB m_bounding_box;

public:
    explicit Sphere(double x_, double y_, double z_, double r_);
    int create() const override;
    aabb::AABB const &getBoundingBox() const override { return m_bounding_box ;}
};

/// @brief Represents Cylinder volume.
class Cylinder final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{}, r{}, angle{};
    int tag{};
    aabb::AABB m_bounding_box;

public:
    explicit Cylinder(double x_, double y_, double z_,
                      double dx_, double dy_, double dz_,
                      double r_, double angle_ = 2 * std::numbers::pi, int tag_ = -1);
    int create() const override;
    aabb::AABB const &getBoundingBox() const override { return m_bounding_box ;}
};

/// @brief Represents Cone volume.
class Cone final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{}, r1{}, r2{}, angle{};
    int tag{};
    aabb::AABB m_bounding_box;

public:
    explicit Cone(double x_, double y_, double z_,
                  double dx_, double dy_, double dz_,
                  double r1_, double r2_, double angle_ = 2 * std::numbers::pi, int tag_ = -1);
    int create() const override;
    aabb::AABB const &getBoundingBox() const override { return m_bounding_box ;}
};

/**
 * @brief Class providing static methods to create various geometric volumes.
 * Volumes include Box, Sphere, Cylinder, and Cone.
 * The methods in this class allow creating these volumes with specified dimensions and parameters.
 */
class VolumeCreator final
{
public:
    /**
     * @brief Creates a box volume with specified dimensions and coordinates.
     *
     * @param x X-coordinate of the box's origin (default: 0).
     * @param y Y-coordinate of the box's origin (default: 0).
     * @param z Z-coordinate of the box's origin (default: 0).
     * @param dx Length along the x-axis (default: 100).
     * @param dy Length along the y-axis (default: 100).
     * @param dz Length along the z-axis (default: 100).
     *
     * @return An integer value indicating the status of the box creation:
     *       - Zero or positive value typically signifies a successful creation.
     *       - Negative value or error code denotes a failure or specific error condition.
     */
    static int createBox(double x = 0, double y = 0, double z = 0,
                         double dx = 100, double dy = 100, double dz = 100);

    /**
     * @brief Creates a sphere volume with specified coordinates and radius.
     *
     * @param x X-coordinate of the sphere's center (default: 0).
     * @param y Y-coordinate of the sphere's center (default: 0).
     * @param z Z-coordinate of the sphere's center (default: 0).
     * @param r Radius of the sphere (default: 0).
     *
     * @return An integer value indicating the status of the sphere creation:
     *         - Zero or positive value typically signifies a successful creation
     *         - Negative value or error code denotes a failure or specific error condition
     */
    static int createSphere(double x = 0, double y = 0, double z = 0, double r = 100);

    /**
     * @brief Creates a cylinder volume with specified coordinates, dimensions, and parameters.
     *
     * @param x X-coordinate of the cylinder's base center (default: 0).
     * @param y Y-coordinate of the cylinder's base center (default: 0).
     * @param z Z-coordinate of the cylinder's base center (default: 0).
     * @param dx Length along the x-axis (default: 100).
     * @param dy Length along the y-axis (default: 100).
     * @param dz Length along the z-axis (default: 100).
     * @param r Radius of the cylinder (default: 10).
     * @param tag Optional tag value (default: -1).
     * @param angle Angle value for the cylinder (default: 2⋅π).
     *
     * @return An integer value indicating the status of the cylinder creation:
     *         - Zero or positive value typically signifies a successful creation
     *         - Negative value or error code denotes a failure or specific error condition
     */
    static int createCylinder(double x = 0, double y = 0, double z = 0,
                              double dx = 100, double dy = 100, double dz = 100, double r = 10,
                              int tag = -1, double angle = 2 * std::numbers::pi);

    /**
     * @brief Creates a cone volume with specified coordinates, dimensions, and parameters.
     *
     * @param x X-coordinate of the cone's base center (default: 0).
     * @param y Y-coordinate of the cone's base center (default: 0).
     * @param z Z-coordinate of the cone's base center (default: 0).
     * @param dx Length along the x-axis (default: 100).
     * @param dy Length along the y-axis (default: 100).
     * @param dz Length along the z-axis (default: 100).
     * @param r1 Radius of the cone's base (default: 10).
     * @param r2 Radius of the cone's top (default: 35).
     * @param tag Optional tag value (default: -1).
     * @param angle Angle value for the cone (default: 2⋅π).
     *
     * @return An integer value indicating the status of the cone creation:
     *       - Zero or positive value typically signifies a successful creation
     *       - Negative value or error code denotes a failure or specific error condition
     */
    static int createCone(double x = 0, double y = 0, double z = 0,
                          double dx = 100, double dy = 100, double dz = 100,
                          double r1 = 10, double r2 = 35, int tag = -1, double angle = 2 * std::numbers::pi);

    /**
     * @brief Creates multiple Sphere objects.
     * @tparam T Type meeting SphereConcept.
     * @param spheres Span of spheres.
     * @return Vector of created sphere tags.
     */
    static std::vector<int> createSpheres(SphereSpan spheres);
};

/**
 * @brief GMSHandler is a RAII (Resource Acquisition Is Initialization) class for managing
 * GMSH initialization and finalization. The constructor initializes GMSH, and the destructor finalizes it.
 * Copy and move operations are deleted to prevent multiple instances from initializing or
 * finalizing GMSH multiple times.
 */
class GMSHVolumeCreator final
{
private:
    class GMSHandler final
    {
    public:
        GMSHandler() { gmsh::initialize(); }
        ~GMSHandler() { gmsh::finalize(); }

        // Preventing multiple initializations/finalizations:
        GMSHandler(GMSHandler const &) = delete;
        GMSHandler &operator=(GMSHandler const &) = delete;
        GMSHandler(GMSHandler &&) noexcept = delete;
        GMSHandler &operator=(GMSHandler &&) noexcept = delete;
    };

    GMSHandler m_handler;         // RAII handler for GMSH
    aabb::AABB m_bounding_volume; // Bounding volume of last created object

public:
    GMSHVolumeCreator() {}
    ~GMSHVolumeCreator() {}

    /**
     * @brief Creates a geometric volume (Sphere, Cylinder, or Cone) and its mesh, then writes the mesh to a file.
     * @param meshSize The target size of the mesh elements.
     * @param meshDim The dimension of the mesh to be generated.
     * @param outputPath The path where the mesh file will be saved.
     * @param x The x-coordinate of the volume's reference point.
     * @param y The y-coordinate of the volume's reference point.
     * @param z The z-coordinate of the volume's reference point.
     * @param r Radius (for Sphere) or radii components (for Cylinder and Cone).
     * @param dx Length along the x-axis (for Cylinder and Cone).
     * @param dy Length along the y-axis (for Cylinder and Cone).
     * @param dz Length along the z-axis (for Cylinder and Cone).
     * @param tag Optional tag value (for Cylinder and Cone).
     * @param angle Angle value (for Cylinder and Cone).
     */
    void createBoxAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                          double x = 0, double y = 0, double z = 0,
                          double dx = 100, double dy = 100, double dz = 100);
    void createSphereAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                             double x = 0, double y = 0, double z = 0, double r = 100);
    void createSpheresAndMesh(SphereSpan spheres, double meshSize,
                              int meshDim, std::string_view outputPath);
    void createCylinderAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                               double x = 0, double y = 0, double z = 0,
                               double dx = 100, double dy = 100, double dz = 100, double r = 10,
                               int tag = -1, double angle = 2 * std::numbers::pi);
    void createConeAndMesh(double meshSize, int meshDim, std::string_view outputPath,
                           double x = 0, double y = 0, double z = 0,
                           double dx = 100, double dy = 100, double dz = 100,
                           double r1 = 10, double r2 = 35, int tag = -1, double angle = 2 * std::numbers::pi);

    /**
     * @brief Retrieves mesh parameters from a specified file.
     *
     * @param filePath The path to the file containing mesh data.
     * @return TriangleMeshParamVector containing mesh parameters.
     */
    TriangleMeshParamVector getMeshParams(std::string_view filePath);

    /**
     * @brief Executes the Gmsh application unless the `-nopopup` argument is provided.
     * @details This method checks the provided arguments for the presence of `-nopopup`.
     *          If `-nopopup` is not found, it initiates the Gmsh graphical user interface.
     *          This is typically used for visualizing and interacting with the Gmsh application directly.
     * @param argc An integer representing the count of command-line arguments.
     * @param argv A constant pointer to a character array, representing the command-line arguments.
     */
    void runGmsh(int argc, char *argv[]);

    /* === Getter for bounding volume. === */
    constexpr aabb::AABB const &getBoundingVolume() const { return m_bounding_volume; }
};

#include "VolumeCreatorImpl.hpp"

#endif // VOLUMECREATOR_HPP
