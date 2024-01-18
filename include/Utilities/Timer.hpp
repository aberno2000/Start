#ifndef TIMER_HPP
#define TIMER_HPP

#include <chrono>
#include <concepts>
#include <functional>

/**
 * @brief A high-resolution timer for measuring elapsed time.
 * The Timer class provides functionality to measure the elapsed time between
 * starting and stopping the timer. It uses the high-resolution clock for precision.
 */
class Timer final
{
private:
    std::chrono::high_resolution_clock::time_point m_start_tp, m_end_tp;
    bool m_isstarted{false};

public:
    /// @brief Defaulted ctor
    Timer() = default;

    /**
     * @brief Starts the timer.
     * Marks the starting point of the timer by recording the current high-resolution time.
     */
    void startTimer();

    /**
     * @brief Stops the timer.
     * Marks the ending point of the timer by recording the current high-resolution time.
     */
    void stopTimer();

    /**
     * @brief Gets the elapsed time in milliseconds.
     * Calculates and returns the elapsed time in milliseconds between the start and stop points.
     * It is necessary to stop the timer before calling this function.
     * @return Elapsed time in milliseconds
     */
    unsigned elaplsedTimeMS() const;
};

/**
 * @brief Measures the execution time of a callable function with the provided arguments.
 * This function executes the given callable object and measures the elapsed time
 * between the start and stop points using a Timer. The result is the elapsed time
 * in milliseconds.
 * @tparam Callable Type of the callable object (function, lambda, etc.)
 * @tparam Args Parameter types for the callable object
 * @param callable The callable object to be measured
 * @param args Arguments to be forwarded to the callable object
 * @return Elapsed time in milliseconds
 */
template <typename Callable, typename... Args>
unsigned int measureExecutionTime(Callable &&callable, Args &&...args)
{
    static_assert(std::is_invocable_v<Callable, Args...>, "Callable must be invocable with Args");

    Timer timer;
    timer.startTimer();
    std::invoke(std::forward<Callable>(callable), std::forward<Args>(args)...);
    timer.stopTimer();
    return timer.elaplsedTimeMS();
}

#endif // !TIMER_HPP
