#ifndef TRILINOSPRINTER_HPP
#define TRILINOSPRINTER_HPP

#include "TrilinosTypes.hpp"

class TrilinosPrinter
{
public:
    /**
     * @brief Prints the contents of a Kokkos matrix.
     * @param view The matrix to print.
     */
    static void printDynRankView(DynRankView const &view);

    /**
     * @brief Prints the contents of a vector of DynRankViews.
     * @param vector The vector of DynRankViews to print.
     */
    static void printDynRankViewVector(DynRankViewVector const &vector);

    /**
     * @brief Prints the contents of a vector of DynRankViews.
     * @param vector The matrix of DynRankViews to print.
     */
    static void printDynRankViewMatrix(DynRankViewMatrix const &matrix);
};

#endif // !TRILINOSPRINTER_HPP
