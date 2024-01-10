#ifndef VOLUMECREATOR_HPP
#define VOLUMECREATOR_HPP

#include <concepts>
#include <numbers>
#include <span>
#include <tuple>
#include <vector>

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
concept SphereConcept = std::tuple_size_v<T> == 4 &&
                        std::is_floating_point_v<std::tuple_element_t<0, T>> &&
                        std::is_floating_point_v<std::tuple_element_t<1, T>> &&
                        std::is_floating_point_v<std::tuple_element_t<2, T>> &&
                        std::is_floating_point_v<std::tuple_element_t<3, T>>;

using SphereVector = std::vector<std::tuple<double, double, double, double>>;
using SphereSpan = std::span<std::tuple<double, double, double, double> const>;

/// @brief Represents Box volume.
class Box final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{};

public:
    explicit Box(double x_, double y_, double z_,
                 double dx_, double dy_, double dz_) : x(x_), y(y_), z(z_),
                                                       dx(dx_), dy(dy_), dz(dz_) {}
    int create() const override;
};

/// @brief Represents Sphere volume.
class Sphere final : public IVolume
{
private:
    double x{}, y{}, z{}, r{};

public:
    explicit Sphere(double x_, double y_, double z_, double r_) : x(x_), y(y_), z(z_), r(r_) {}
    int create() const override;
};

/// @brief Represents Cylinder volume.
class Cylinder final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{}, r{}, angle{};
    int tag{};

public:
    explicit Cylinder(double x_, double y_, double z_,
                      double dx_, double dy_, double dz_,
                      double r_, double angle_ = 2 * std::numbers::pi, int tag_ = -1)
        : x(x_), y(y_), z(z_),
          dx(dx_), dy(dy_), dz(dz_),
          r(r_), angle(angle_), tag(tag_) {}
    int create() const override;
};

/// @brief Represents Cone volume.
class Cone final : public IVolume
{
private:
    double x{}, y{}, z{}, dx{}, dy{}, dz{}, r1{}, r2{}, angle{};
    int tag{};

public:
    explicit Cone(double x_, double y_, double z_,
                  double dx_, double dy_, double dz_,
                  double r1_, double r2_, double angle_ = 2 * std::numbers::pi, int tag_ = -1)
        : x(x_), y(y_), z(z_),
          dx(dx_), dy(dy_), dz(dz_),
          r1(r1_), r2(r2_), angle(angle_), tag(tag_) {}
    int create() const override;
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
    static int createSphere(double x = 0, double y = 0, double z = 0, double r = 0);

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
     * @param x X-coordinate of the cone's base center.
     * @param y Y-coordinate of the cone's base center.
     * @param z Z-coordinate of the cone's base center.
     * @param dx Length along the x-axis.
     * @param dy Length along the y-axis.
     * @param dz Length along the z-axis.
     * @param r1 Radius of the cone's base.
     * @param r2 Radius of the cone's top.
     * @param tag Optional tag value (default: -1).
     * @param angle Angle value for the cone (default: 2⋅π).
     *
     * @return An integer value indicating the status of the cone creation:
     *       - Zero or positive value typically signifies a successful creation
     *       - Negative value or error code denotes a failure or specific error condition
     */
    static int createCone(double x, double y, double z,
                          double dx, double dy, double dz,
                          double r1, double r2, int tag = -1, double angle = 2 * std::numbers::pi);

    /**
     * @brief Creates multiple Sphere objects.
     * @tparam T Type meeting SphereConcept.
     * @param spheres Span of spheres.
     * @return Vector of created sphere tags.
     */
    template <SphereConcept T>
    static std::vector<int> createSpheres(std::span<T const> spheres);
};

#include "VolumeCreatorImpl.hpp"

#endif // VOLUMECREATOR_HPP
