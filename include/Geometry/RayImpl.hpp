#ifndef RAYIMPL_HPP
#define RAYIMPL_HPP

#include <limits>

template <typename T>
Ray<T>::Ray(Point<T> const &A, Point<T> const &B)
    : m_A(A), m_B(B), m_ray(Ray3(Point3(m_A.x,
                                        m_A.y,
                                        m_A.z),
                                 Point3(m_B.x,
                                        m_B.y,
                                        m_B.z))) {}

template <typename T>
Ray<T>::Ray(Point<T> &&A, Point<T> &&B) noexcept
    : m_A(std::move(A)), m_B(std::move(B)), m_ray(Ray3(Point3(m_A.x,
                                                              m_A.y,
                                                              m_A.z),
                                                       Point3(m_B.x,
                                                              m_B.y,
                                                              m_B.z))) {}

template <typename T>
constexpr Point<T> const &Ray<T>::getA() const { return m_A; }

template <typename T>
constexpr Point<T> const &Ray<T>::getB() const { return m_B; }

template <typename T>
constexpr Ray3 const &Ray<T>::getRayCGAL() const { return m_ray; }

using RayF = Ray<float>;
using RayD = Ray<double>;

#endif // !RAYIMPL_HPP
