#ifndef VOLUMECREATOR_HPP
#define VOLUMECREATOR_HPP

#include <concepts>
#include <numbers>
#include <span>
#include <tuple>
#include <vector>

class IVolume
{
public:
    virtual int create() const = 0;
    virtual ~IVolume() {}
};

template <typename T>
concept SphereConcept = std::tuple_size<T>::value == 4 &&
                        std::is_floating_point_v<std::tuple_element_t<0, T>>;

using SphereVector = std::vector<std::tuple<double, double, double, double>>;
using SphereSpan = std::span<std::tuple<double, double, double, double> const>;

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

class Sphere final : public IVolume
{
private:
    double x{}, y{}, z{}, r{};

public:
    explicit Sphere(double x_, double y_, double z_, double r_) : x(x_), y(y_), z(z_), r(r_) {}
    int create() const override;
};

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

class VolumeCreator final
{
public:
    static int createBox(double x = 0, double y = 0, double z = 0,
                         double dx = 100, double dy = 100, double dz = 100);
    static int createSphere(double x = 0, double y = 0, double z = 0, double r = 0);
    static int createCylinder(double x = 0, double y = 0, double z = 0,
                              double dx = 100, double dy = 100, double dz = 100, double r = 10,
                              int tag = -1, double angle = 2 * std::numbers::pi);
    static int createCone(double x, double y, double z,
                          double dx, double dy, double dz,
                          double r1, double r2, int tag = -1, double angle = 2 * std::numbers::pi);

    template <SphereConcept T>
    static std::vector<int> createSpheres(std::span<T const> spheres);
};

#include "VolumeCreatorImpl.hpp"

#endif // VOLUMECREATOR_HPP
