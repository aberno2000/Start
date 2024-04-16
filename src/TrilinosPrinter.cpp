#include "../include/Utilities/TrilinosPrinter.hpp"

void TrilinosPrinter::printDynRankView(DynRankView const &view)
{
    auto numRows{view.extent(0)};
    auto numCols{view.extent(1)};

    for (size_t i{}; i < numRows; ++i)
    {
        for (size_t j{}; j < numCols; ++j)
            std::cout << view(i, j) << ' ';
        std::endl(std::cout);
    }
}

void TrilinosPrinter::printDynRankViewVector(DynRankViewVector const &vector)
{
    size_t i{};
    for (const auto &view : vector)
    {
        std::cout << "DynRankView[" << i++ << "]\n";
        printDynRankView(view);
    }
}

void TrilinosPrinter::printDynRankViewMatrix(DynRankViewMatrix const &matrix)
{
    size_t i{}, j{};
    for (const auto &vector : matrix)
    {
        for (const auto &view : vector)
        {
            std::cout << "DynRankView[" << i++ << "][" << j++ << "]\n";
            printDynRankView(view);
        }
        std::endl(std::cout);
    }
}
