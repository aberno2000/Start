#include <cassert>

#include "../include/Timer.hpp"

void Timer::startTimer()
{
    m_isstarted = true;
    m_start_tp = std::chrono::high_resolution_clock::now();
}

void Timer::stopTimer()
{
    m_isstarted = false;
    m_end_tp = std::chrono::high_resolution_clock::now();
}

unsigned Timer::elaplsedTimeMS() const
{
    assert(!m_isstarted);
    auto elapsed{m_end_tp - m_start_tp};
    auto ms{std::chrono::duration_cast<std::chrono::milliseconds>(elapsed)};
    return ms.count();
}
