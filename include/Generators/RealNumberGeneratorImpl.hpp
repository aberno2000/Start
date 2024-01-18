#ifndef REALNUMBERGENERATORIMPL_HPP
#define REALNUMBERGENERATORIMPL_HPP

constexpr void RealNumberGenerator::set_lower_bound(double val) { m_from = val; }

constexpr void RealNumberGenerator::set_upper_bound(double val) { m_to = val; }

constexpr void RealNumberGenerator::set(double from, double to)
{
    m_from = from;
    m_to = to;
}

#endif // !REALNUMBERGENERATORIMPL_HPP
