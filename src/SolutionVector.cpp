#include "../include/Utilities/SolutionVector.hpp"

SolutionVector::SolutionVector(size_t size)
    : m_comm(Tpetra::getDefaultComm()),
      m_map(new MapType(size, 0, m_comm)), // 0 here is the index base.
      m_solution_vector(Teuchos::rcp(new TpetraVectorType(m_map)))
{
}

void SolutionVector::setBoundaryConditions(std::map<LocalOrdinal, Scalar> const &boundaryConditions)
{
    if (boundaryConditions.empty())
        return;

    // Setting boundary conditions to solution vector:
    for (auto const &[nodeID, value] : boundaryConditions)
        // -1 because indexing in GMSH is on 1 bigger than in the program.
        m_solution_vector->replaceGlobalValue(nodeID - 1, value); // Modifying the RHS vector is necessary to solve the equation Ax=b.
}

size_t SolutionVector::size() const { return m_solution_vector->getGlobalLength(); }

void SolutionVector::randomize() { m_solution_vector->randomize(); }

void SolutionVector::clear() { m_solution_vector->putScalar(0.0); }

void SolutionVector::print() const
{
    int myRank{m_comm->getRank()};
    int numProcs{m_comm->getSize()};

    // Synchronize all processes before printing.
    m_comm->barrier();
    for (int proc{}; proc < numProcs; ++proc)
    {
        if (myRank == proc)
        {
            // Only the current process prints its portion of the vector.
            std::cout << std::format("Process {}\n", myRank);

            // Printing using describe() for detailed information.
            Teuchos::RCP<Teuchos::FancyOStream> out{Teuchos::fancyOStream(Teuchos::rcpFromRef(std::cout))};
            m_solution_vector->describe(*out, Teuchos::VERB_EXTREME);

            // Printing individual elements
            auto vecView{m_solution_vector->getLocalViewHost(Tpetra::Access::ReadOnly)};
            auto vecData{vecView.data()};
            size_t localLength{m_solution_vector->getLocalLength()};
            for (size_t i{}; i < localLength; ++i)
                std::cout << std::format("Element {}: {}\n", i, vecData[i]);
        }
        // Synchronize before the next process starts printing.
        m_comm->barrier();
    }
    // Final barrier to ensure printing is finished before proceeding.
    m_comm->barrier();
}
