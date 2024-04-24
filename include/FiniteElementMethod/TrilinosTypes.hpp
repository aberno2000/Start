#ifndef TRILINOS_TYPES_HPP
#define TRILINOS_TYPES_HPP

#include <BelosSolverFactory.hpp>
#include <BelosTpetraAdapter.hpp>
#include <Intrepid2_CellTools.hpp>
#include <Intrepid2_DefaultCubatureFactory.hpp>
#include <Intrepid2_FunctionSpaceTools.hpp>
#include <Intrepid2_HGRAD_TET_C1_FEM.hpp>
#include <Intrepid2_HGRAD_TET_C2_FEM.hpp>
#include <Intrepid2_HGRAD_TET_Cn_FEM.hpp>
#include <Intrepid_FunctionSpaceTools.hpp>
#include <Kokkos_Core.hpp>
#include <Panzer_DOFManager.hpp>
#include <Panzer_IntrepidFieldPattern.hpp>
#include <Shards_CellTopology.hpp>
#include <Teuchos_GlobalMPISession.hpp>
#include <Teuchos_ParameterList.hpp>
#include <Teuchos_RCP.hpp>
#include <Tpetra_Core.hpp>
#include <Tpetra_CrsMatrix.hpp>
#include <Tpetra_Map.hpp>
#include <Tpetra_Vector.hpp>
#include <array>
#include <vector>

using Scalar = double;                                                // ST - Scalar Type (type of the data inside the matrix node).
using LocalOrdinal = int;                                             // LO - indices in local matrix.
using GlobalOrdinal = long long;                                      // GO - Global Ordinal Type (indices in global matrices).
using ExecutionSpace = Kokkos::DefaultExecutionSpace;                 // Using host space to interoperate with data.
using DeviceType = Kokkos::Device<ExecutionSpace, Kokkos::HostSpace>; // Using CPU.
using DynRankView = Kokkos::DynRankView<Scalar, DeviceType>;          // Multi-dimensional array template.
using DynRankViewVector = std::vector<DynRankView>;                   // Vector of multi-dimensional arrays.
using DynRankViewMatrix = std::vector<DynRankViewVector>;             // Matrix of multi-dimensional arrays.
using Node = Tpetra::Map<>::node_type;                                // Node type based on Kokkos execution space.
using MapType = Tpetra::Map<LocalOrdinal, GlobalOrdinal, Node>;
using TpetraVectorType = Tpetra::Vector<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraMultiVector = Tpetra::MultiVector<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraOperator = Tpetra::Operator<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TpetraMatrixType = Tpetra::CrsMatrix<Scalar, LocalOrdinal, GlobalOrdinal, Node>;
using TetrahedronIndices = std::array<LocalOrdinal, 4ul>;
using TetrahedronIndicesVector = std::vector<TetrahedronIndices>;
using Commutator = Teuchos::RCP<Teuchos::Comm<int> const>;

#endif // !TRILINOS_TYPES_HPP
