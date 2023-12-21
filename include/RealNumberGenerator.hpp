#ifndef REALNUMBERGENERATOR_HPP
#define REALNUMBERGENERATOR_HPP

#include <random>
#include <vector>

/// @brief Generator for real numbers and their sequences.
class RealNumberGenerator final
{
private:
    double m_from{kdefault_min_value}, // Lower bound.
        m_to{kdefault_max_value};      // Upper bound.
    std::random_device m_rdm_dev;      // Special engine that requires a piece of attached hardware to PC
                                       // that generates truly non-deterministic random numbers.
    std::mt19937 m_engine;             // Mersenne Twister engine:
                                       // Fastest.
                                       // T = 2^19937 - 1 (The period of the pseudorandom sequence).
                                       // Memory usage ~2.5kB.

    static constexpr double kdefault_min_value{0.0}; // Default value of the lower bound.
    static constexpr double kdefault_max_value{1.0}; // Default value of the upper bound.

public:
    RealNumberGenerator();
    RealNumberGenerator(double from, double to);
    ~RealNumberGenerator() {}

    /**
     * @brief Generates one random real number in specified interval (from, to).
     * Usage:
     * RealNumberGenerator rng;
     * rng(); -> by default generates real numbers in (0.0, 1.0)
     * rng.set_lower_bound(0.5);
     * rng(); -> now generates real number in interval (0.5, 1.0)
     */
    double operator()();

    /**
     * @brief Generates one random real number in interval (from, to).
     * @param from lower bound.
     * @param to upper bound.
     */
    double get_double(double from, double to);

    /* === Setter methods for data members === */
    constexpr void set_lower_bound(double val) { m_from = val; }
    constexpr void set_upper_bound(double val) { m_to = val; }
    constexpr void set(double from, double to)
    {
        m_from = from;
        m_to = to;
    }

    /**
     * @brief Generates sequence of real numbers in specified interval.
     * @param count Count of numbers to generate.
     */
    std::vector<double> get_sequence(size_t count, double from = 0.0, double to = 1.0);
};

#endif // !REALNUMBERGENERATOR_HPP
