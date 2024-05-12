#include "../include/FiniteElementMethod/SolutionVector.hpp"
#include "../include/Utilities/Utilities.hpp"

SolutionVector::SolutionVector(size_t size, short polynomOrder)
    : m_comm(Tpetra::getDefaultComm()),
      m_map(new MapType(size, 0, m_comm)), // 0 here is the index base.
      m_solution_vector(Teuchos::rcp(new TpetraVectorType(m_map))),
      m_polynomOrder(polynomOrder)
{
    if (polynomOrder <= 0)
    {
        ERRMSG("Polynom order can't be negative or equals to 0");
        throw std::runtime_error("Polynom order can't be negative or equals to 0");
    }
}

void SolutionVector::setBoundaryConditions(std::map<GlobalOrdinal, Scalar> const &boundaryConditions)
{
    if (boundaryConditions.empty())
    {
        WARNINGMSG("Boundary conditions are empty, check them, maybe you forgot to fill them");
        return;
    }

    try
    {
        // Setting boundary conditions to solution vector:
        for (auto const &[nodeInGmsh, value] : boundaryConditions)
            for (int j{}; j < m_polynomOrder; ++j)
            {
                // -1 because indexing in GMSH is on 1 bigger than in the program.
                LocalOrdinal nodeID{(nodeInGmsh - 1) * m_polynomOrder + j};

                if (nodeID >= static_cast<LocalOrdinal>(size()))
                    throw std::runtime_error(util::stringify("Boundary condition refers to node index ",
                                                             nodeID,
                                                             ", which exceeds the maximum row index of ",
                                                             size() - 1, "."));

                m_solution_vector->replaceGlobalValue(nodeID, value); // Modifying the RHS vector is necessary to solve the equation Ax=b.
            }
    }
    catch (std::exception const &ex)
    {
        ERRMSG(ex.what());
    }
    catch (...)
    {
        ERRMSG("Unknown error was occured while trying to apply boundary conditions on solution vector (`b`) in equation Ax=b");
    }
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
