#include <algorithm>
#include <chrono>
#include <format>
#include <functional>
#include <iostream>
#include <ranges>

#include "../include/Generators/RealNumberGenerator.hpp"

// `.entropy()` returns 0.0 if random device using a software-based pseudorandom generator
RealNumberGenerator::RealNumberGenerator() : m_engine(m_rdm_dev.entropy() ? m_rdm_dev() : time(nullptr)) {}

RealNumberGenerator::RealNumberGenerator(double from, double to) : m_from(from), m_to(to) {}

double RealNumberGenerator::operator()() { return get_double(m_from, m_to); }

double RealNumberGenerator::operator()(double from, double to) { return get_double(from, to); }

double RealNumberGenerator::get_double(double from, double to) { return std::uniform_real_distribution(from, to)(m_engine); }

std::vector<double> RealNumberGenerator::get_sequence(size_t count, double from, double to)
{
    if (count == 0ul)
        return {};

    std::vector<double> v(count);
    std::ranges::generate(v, std::bind(std::uniform_real_distribution<double>(from, to), m_engine));
    return v;
}
