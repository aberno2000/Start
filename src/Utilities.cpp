#include <chrono>
#include <sstream>
#include <sys/stat.h>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Utilities/ConfigParser.hpp"
#include "../include/Utilities/Utilities.hpp"

std::string util::getCurTime(std::string_view format)
{
    std::chrono::system_clock::time_point tp{std::chrono::system_clock::now()};
    time_t tt{std::chrono::system_clock::to_time_t(tp)};
    tm *t{localtime(&tt)};
    std::stringstream ss;
    ss << std::put_time(t, std::string(format).c_str());
    return ss.str();
}

std::string util::getStatusName(double status)
{
    switch (static_cast<int>(status))
    {
    case -8:
        return "BAD_VOLUME";
    case -7:
        return "BAD_PRESSURE";
    case -6:
        return "BAD_TEMPERATURE";
    case -5:
        return "BAD_ENERGY";
    case -4:
        return "BAD_MODEL";
    case -3:
        return "UNKNOWN_PARTICLES";
    case -2:
        return "BAD_PARTICLES_FORMAT";
    case -1:
        return "BAD_FILE";
    case 0:
        return "EMPTY_STR";
    case 1:
        return "STATUS_OK";
    default:
        return "UNKNOWN_STATUS";
    }
}

ParticleType util::getParticleTypeFromStrRepresentation(std::string_view particle)
{
    if (particle == "Ar")
        return Ar;
    else if (particle == "Ne")
        return Ne;
    else if (particle == "He")
        return He;
    else if (particle == "Ti")
        return Ti;
    else if (particle == "Al")
        return Al;
    else if (particle == "Sn")
        return Sn;
    else if (particle == "W")
        return W;
    else if (particle == "Au")
        return Au;
    else if (particle == "Cu")
        return Cu;
    else if (particle == "Ni")
        return Ni;
    else if (particle == "Ag")
        return Ag;
    else
        return Unknown;
}

std::string util::getParticleType(ParticleType ptype)
{
    switch (ptype)
    {
    case Ar:
        return "Ar";
    case Ne:
        return "Ne";
    case He:
        return "He";
    case Ti:
        return "Ti";
    case Al:
        return "Al";
    case Sn:
        return "Sn";
    case W:
        return "W";
    case Au:
        return "Au";
    case Ni:
        return "Ni";
    case Ag:
        return "Ag";
    default:
        return "Unknown";
    }
}

double util::calculateConcentration(std::string_view config)
{
    ConfigParser parser(config);
    if (parser.isInvalid())
        return -1.0;

    // n = PV/RT * N_Avogadro
    return parser.getPressure() * parser.getVolume() * constants::physical_constants::N_av /
           (parser.getTemperature() * constants::physical_constants::R);
}

bool util::exists(std::string_view filename)
{
#ifdef __unix__
    struct stat buf;
    return (stat(filename.data(), std::addressof(buf)) == 0);
#endif
#ifdef _WIN32
    struct _stat buf;
    return (_stat(filename.data(), std::addressof(buf)) == 0);
#endif
}

double util::calculateVolumeOfTetrahedron3(Tetrahedron3 const &tetrahedron)
{
    Point3 const &A{tetrahedron[0]},
        &B{tetrahedron[1]},
        &C{tetrahedron[2]},
        &D{tetrahedron[3]};

    // Construct vectors AB, AC, and AD
    Kernel::Vector_3 AB{B - A}, AC{C - A}, AD{D - A};

    // Compute the scalar triple product (AB . (AC x AD))
    double scalarTripleProduct{CGAL::scalar_product(AB, CGAL::cross_product(AC, AD))};

    // The volume of the tetrahedron is the absolute value of the scalar triple product divided by 6
    return std::abs(scalarTripleProduct) / 6.0;
}

void util::printMatrix(const Kokkos::DynRankView<double, DeviceType> &matrix)
{
    auto numRows{matrix.extent(0)};
    auto numCols{matrix.extent(1)};

    for (size_t i{}; i < numRows; ++i)
    {
        for (size_t j{}; j < numCols; ++j)
            std::cout << matrix(i, j) << " ";
        std::cout << std::endl;
    }
}

std::pair<std::vector<Kokkos::DynRankView<double, DeviceType>>, Kokkos::DynRankView<double, DeviceType>>
util::computeTetrahedronBasisFunctions(MeshTetrahedronParam const &meshParam)
{
    // Defining cell topology as tetrahedron.
    shards::CellTopology cellType{shards::getCellTopologyData<shards::Tetrahedron<>>()};
    Intrepid2::Basis_HGRAD_TET_C1_FEM<DeviceType> basis;

    // Using cubature factory to create cubature function.
    Intrepid2::DefaultCubatureFactory cubFactory;
    auto cubature{cubFactory.create<DeviceType>(cellType.getBaseKey(), basis.getDegree())};

    auto numCubPoints{cubature->getNumPoints()}; // Getting number of cubature points.
    auto spaceDim{cubature->getDimension()};     // Getting dimension (for tetrahedron, obviously - 3D).

    // Allocating memory for cubature poinst and weights.
    Kokkos::DynRankView<double, DeviceType> cubPoints("cubPoints", numCubPoints, spaceDim);
    Kokkos::DynRankView<double, DeviceType> cubWeights("cubWeights", numCubPoints);

    // Allocating memory for values of basis functions.
    auto numFields{basis.getCardinality()};
    Kokkos::DynRankView<double, DeviceType> basisValues("basisValues", numFields, numCubPoints);
    Kokkos::DynRankView<double, DeviceType> transformedBasisValues("transformedBasisValues", 1, numFields, numCubPoints);

    // Getting cubature points and weights.
    cubature->getCubature(cubPoints, cubWeights);

    // Getting tetrahedron coordinates of each vertex.
    Kokkos::DynRankView<double, DeviceType> vertices("vertices", 1, 4, 3);
    auto tetrahedron{std::get<1>(meshParam)};
    for (size_t node{}; node < 4; ++node)
    {
        vertices(0, node, 0) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).x());
        vertices(0, node, 1) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).y());
        vertices(0, node, 2) = CGAL_TO_DOUBLE(tetrahedron.vertex(node).z());
    }

    // Calculating basis functions on cubature points.
    basis.getValues(basisValues, cubPoints, Intrepid2::OPERATOR_VALUE);
    std::vector<Kokkos::DynRankView<double, DeviceType>> basisFunctionsValues;
    for (Intrepid2::ordinal_type i{}; i < numFields; ++i)
    {
        Kokkos::DynRankView<double, DeviceType> fieldValues("fieldValues", numCubPoints);
        for (Intrepid2::ordinal_type j{}; j < numCubPoints; ++j)
            fieldValues(j) = basisValues(i, j);
        basisFunctionsValues.emplace_back(fieldValues);
    }

    // Transforming basis functions from relative values to physical space.
    Intrepid2::CellTools<DeviceType>::mapToPhysicalFrame(transformedBasisValues, cubPoints, vertices, cellType);

    // Opt: printing transformed basis values in all cubature points.
    for (Intrepid2::ordinal_type i{}; i < numFields; ++i)
        for (Intrepid2::ordinal_type j{}; j < numCubPoints; ++j)
            std::cout << std::format("Tetrahedron[{}]: ", std::get<0>(meshParam))
                      << "Transformed basis function " << i << " at cubature point " << j
                      << " = " << transformedBasisValues(0, i, j) << std::endl;
    return std::make_pair(basisFunctionsValues, cubWeights);
}

Kokkos::DynRankView<double, DeviceType> util::computeLocalStiffnessMatrix(
    std::vector<Kokkos::DynRankView<double, DeviceType>> const &basisGradients,
    Kokkos::DynRankView<double, DeviceType> const &cubWeights)
{
    // Getting count of basis functions and count of cubature points.
    auto const numFields{basisGradients.size()};
    auto const numCubPoints{cubWeights.extent(0)};

    Kokkos::DynRankView<double, DeviceType> localStiffnessMatrix("localStiffnessMatrix", numFields, numFields); // Creating local stiffness matrix.
    Kokkos::deep_copy(localStiffnessMatrix, 0.0);                                                               // Initialization of local stiffness matrix with nulls.

    // Calculating local stiffness matrix.
    for (size_t i{}; i < numFields; ++i)
        for (size_t j{}; j < numFields; ++j)
            for (size_t qp{}; qp < numCubPoints; ++qp)
                for (size_t d{}; d < 3; ++d)
                    localStiffnessMatrix(i, j) += basisGradients[i](qp, d) * basisGradients[j](qp, d) * cubWeights(qp);
    /* std::cout << std::format("Local stiffness matrix for tetrahedron[{}]\n", std::get<0>(meshParam));
    printMatrix(localStiffnessMatrix); */

    return localStiffnessMatrix;
}

SpMat util::assembleGlobalStiffnessMatrix(
    MeshTetrahedronParamVector const &meshParams,
    std::vector<std::vector<Kokkos::DynRankView<double, DeviceType>>> const &allBasisGradients,
    std::vector<Kokkos::DynRankView<double, DeviceType>> const &allCubWeights,
    int totalNodes,
    std::vector<std::array<int, 4>> const &globalNodeIndicesPerElement)
{
    // Initialization of the global stiffness matrix.
    SpMat globalStiffnessMatrix(totalNodes, totalNodes);

    // List for store non-null elements.
    std::vector<Eigen::Triplet<double>> tripletList;
    for (size_t elemIndex{}; elemIndex < meshParams.size(); ++elemIndex)
    {
        // Calculating local stiffness matrix.
        auto localStiffnessMatrix{computeLocalStiffnessMatrix(allBasisGradients[elemIndex], allCubWeights[elemIndex])};

        // Indeces of global nodes for the current tetrahedron.
        auto const &globalNodeIndices{globalNodeIndicesPerElement[elemIndex]};

        // Adding local stiffness matrix to the global.
        for (int i{}; i < 4; ++i)
            for (int j{}; j < 4; ++j)
                tripletList.emplace_back(
                    globalNodeIndices[i],
                    globalNodeIndices[j],
                    localStiffnessMatrix(i, j));
    }

    // Assemblying global matrix from the triplets.
    globalStiffnessMatrix.setFromTriplets(tripletList.begin(), tripletList.end());
    return globalStiffnessMatrix;
}

void util::fillVectorWithRandomNumbers(Eigen::VectorXd &b, int size, double lower, double upper)
{
    RealNumberGenerator rng;
    b.resize(size);
    for (int i{}; i < size; ++i)
        b(i) = rng(lower, upper);
}

TpetraMatrixType util::convertEigenToTpetra(SpMat const &eigenMatrix)
{
    auto comm{Tpetra::getDefaultComm()};
    auto const numGlobalEntries{eigenMatrix.rows()};
    Teuchos::RCP<MapType> map(new MapType(numGlobalEntries, 0, comm));
    TpetraMatrixType tpetraMatrix(map, numGlobalEntries);

    // Insert values from Eigen matrix into Tpetra matrix
    for (int k{}; k < eigenMatrix.outerSize(); ++k)
        for (Eigen::SparseMatrix<double>::InnerIterator it(eigenMatrix, k); it; ++it)
            tpetraMatrix.insertGlobalValues(it.row(), Teuchos::tuple<GlobalOrdinal>(it.col()), Teuchos::tuple<Scalar>(it.value()));

    // Finilize matrix assembly.
    tpetraMatrix.fillComplete();

    // Printing matrix.
    Teuchos::RCP<Teuchos::FancyOStream> out = Teuchos::fancyOStream(Teuchos::rcpFromRef(std::cout));
    tpetraMatrix.describe(*out, Teuchos::VERB_HIGH);

    return tpetraMatrix;
}

void util::printLocalMatrixEntries(TpetraMatrixType const &matrix)
{
    auto comm{matrix.getMap()->getComm()};
    auto myRank{comm->getRank()};
    auto numProcs{comm->getSize()};

    // Loop over all processes in sequential order.
    for (int proc{}; proc < numProcs; ++proc)
    {
        if (myRank == proc)
        {
            // Print the matrix entries for the current process.
            auto rowMap{matrix.getRowMap()};
            size_t localNumRows{rowMap->getLocalNumElements()};

            for (size_t i{}; i < localNumRows; ++i)
            {
                GlobalOrdinal globalRow{rowMap->getGlobalElement(i)};
                size_t numEntries{matrix.getNumEntriesInGlobalRow(globalRow)};

                typename TpetraMatrixType::nonconst_global_inds_host_view_type indices("ind", numEntries);
                typename TpetraMatrixType::nonconst_values_host_view_type values("val", numEntries);
                size_t checkNumEntries{};

                matrix.getGlobalRowCopy(globalRow, indices, values, checkNumEntries);

                // Now print the row's entries
                std::cout << "Row " << globalRow << ": ";
                for (size_t k{}; k < checkNumEntries; ++k)
                    std::cout << "(" << indices[k] << ", " << values[k] << ") ";
                std::endl(std::cout);
            }
        }
        // Synchronize all processes.
        comm->barrier();
    }
}

void util::printTpetraVector(TpetraVectorType const &vec)
{
    auto comm{vec.getMap()->getComm()};
    int myRank{comm->getRank()};
    int numProcs{comm->getSize()};

    // Synchronize all processes before printing.
    comm->barrier();
    for (int proc{}; proc < numProcs; ++proc)
    {
        if (myRank == proc)
        {
            // Only the current process prints its portion of the vector.
            std::cout << std::format("Process {}\n", myRank);

            // Printing using describe() for detailed information.
            Teuchos::RCP<Teuchos::FancyOStream> out = Teuchos::fancyOStream(Teuchos::rcpFromRef(std::cout));
            vec.describe(*out, Teuchos::VERB_EXTREME);

            // Printing individual elements
            auto vecView{vec.getLocalViewHost(Tpetra::Access::ReadOnly)};
            auto vecData{vecView.data()};
            size_t localLength{vec.getLocalLength()};
            for (size_t i{}; i < localLength; ++i)
                std::cout << "Element " << i << ": " << vecData[i] << std::endl;
        }
        // Synchronize before the next process starts printing.
        comm->barrier();
    }
    // Final barrier to ensure printing is finished before proceeding.
    comm->barrier();
}
