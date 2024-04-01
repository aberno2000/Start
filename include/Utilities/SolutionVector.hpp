#ifndef SOLUTION_VECTOR_HPP
#define SOLUTION_VECTOR_HPP

#include "TrilinosTypes.hpp"

class SolutionVector
{
private:
    Commutator m_comm;                                ///< Handles inter-process communication within a parallel computing environment. MPI communicator.
    Teuchos::RCP<MapType> m_map;                      ///< A smart pointer managing the lifetime of a Map object, which defines the layout of distributed data across the processes in a parallel computation.
    Teuchos::RCP<TpetraVectorType> m_solution_vector; ///< Solution vector `b` in the equation: Ax=b. Where `A` - global stiffness matrix; `x` - vector to find; `b` - solution vector.

public:
    SolutionVector(size_t size);
    ~SolutionVector() {}

    /**
     * @brief Sets the boundary conditions to the solution vector. Changes specified values from map.
     * @param boundaryConditions Map for the boundary conditions. Key - ID of diagonal element (row and col). Value - value to be assigned.
     */
    void setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions);

    /**
     * @brief Getter for size of the vector.
     * @return Size of the vector.
     */
    size_t size() const;

    /// @brief Assigns random values to all elements of the vector.
    void randomize();

    /// @brief Zeros out all the elements in the vector.
    void clear();

    /// @brief Prints the contents of a Tpetra vector.
    void print() const;

    /// @brief Getter for solution vector.
    constexpr Teuchos::RCP<TpetraVectorType> const &getSolutionVector() const { return m_solution_vector; }
};

#endif // !SOLUTION_VECTOR_HPP
