#ifndef TRIANGLEIMPL_HPP
#define TRIANGLEIMPL_HPP

template <typename T>
Triangle<T>::Triangle(Point<T> const &A, Point<T> const &B, Point<T> const &C)
    : m_A(A), m_B(B), m_C(C),
      m_triangle(Point3(m_A.x, m_A.y, m_A.z),
                 Point3(m_B.x, m_B.y, m_B.z),
                 Point3(m_C.x, m_C.y, m_C.z)) {}

template <typename T>
Triangle<T>::Triangle(Point<T> &&A, Point<T> &&B, Point<T> &&C) noexcept
    : m_A(std::move(A)), m_B(std::move(B)), m_C(std::move(C)),
      m_triangle(Point3(m_A.x, m_A.y, m_A.z),
                 Point3(m_B.x, m_B.y, m_B.z),
                 Point3(m_C.x, m_C.y, m_C.z)) {}

template <typename T>
constexpr Point<T> const &Triangle<T>::getA() const { return m_A; }

template <typename T>
constexpr Point<T> const &Triangle<T>::getB() const { return m_B; }

template <typename T>
constexpr Point<T> const &Triangle<T>::getC() const { return m_C; }

template <typename T>
constexpr Triangle3 const &Triangle<T>::getTriangleCGAL() const { return m_triangle; }

using TriangleF = Triangle<float>;
using TriangleD = Triangle<double>;

#endif // !TRIANGLEIMPL_HPP
