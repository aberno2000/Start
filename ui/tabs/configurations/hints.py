from .default_field_values import *
from .limitations import *

HINT_CONFIG_MAX_ITERATIONS = (
    f"Max Iterations: The maximum number of iterations the solver will perform. "
    f"Range: {LIMIT_CONFIG_MIN_ITERATIONS} to {LIMIT_CONFIG_MAX_ITERATIONS}.")
HINT_CONFIG_CONVERGENCE_TOLERANCE = (
    f"Convergence Tolerance: The tolerance for the relative residual norm used to determine convergence. "
    f"Range: {LIMIT_CONFIG_MIN_CONVERGENCE_TOLERANCE} to {LIMIT_CONFIG_MAX_CONVERGENCE_TOLERANCE}."
)
HINT_CONFIG_OUTPUT_FREQUENCY = (
    f"Output Frequency: Determines how often information is printed during the iterative process. "
    f"Range: {LIMIT_CONFIG_MIN_OUTPUT_FREQUENCY} to {LIMIT_CONFIG_MAX_OUTPUT_FREQUENCY}."
)
HINT_CONFIG_NUM_BLOCKS = (
    f"Num Blocks: Sets the number of blocks in the Krylov basis, related to the restart mechanism of GMRES. "
    f"Range: {LIMIT_CONFIG_MIN_NUM_BLOCKS} to {LIMIT_CONFIG_MAX_NUM_BLOCKS}.")
HINT_CONFIG_BLOCK_SIZE = (
    f"Block Size: Determines the block size for block methods. "
    f"Range: {LIMIT_CONFIG_MIN_BLOCK_SIZE} to {LIMIT_CONFIG_MAX_BLOCK_SIZE}.")
HINT_CONFIG_MAX_RESTARTS = (
    f"Max Restarts: Specifies the maximum number of restarts allowed. "
    f"Range: {LIMIT_CONFIG_MIN_MAX_RESTARTS} to {LIMIT_CONFIG_MAX_MAX_RESTARTS}."
)
HINT_CONFIG_FLEXIBLE_GMRES = "Flexible GMRES: Indicates whether to use the flexible version of GMRES. Options: true, false."
HINT_CONFIG_ORTHOGONALIZATION = "Orthogonalization: Specifies the orthogonalization method to use. Options: ICGS, IMGS."
HINT_CONFIG_ADAPTIVE_BLOCK_SIZE = "Adaptive Block Size: Indicates whether to adapt the block size in block methods. Options: true, false."
HINT_CONFIG_CONVERGENCE_TEST_FREQUENCY = "Convergence Test Frequency: Specifies how often convergence is tested (in iterations). Default setting is used if negative. Range: -1 or positive integers."

HINT_CONFIG_SOLVERNAME = (
    "CG (Conjugate Gradient): Used for solving systems of linear equations with symmetric positive-definite matrices.\n"
    "Block CG: A variant of CG that handles multiple right-hand sides simultaneously.\n"
    "GMRES (Generalized Minimal Residual): Suitable for non-symmetric or indefinite matrices, minimizes the residual over a Krylov subspace.\n"
    "Block GMRES: A block version of GMRES for multiple right-hand sides.\n"
    "LSQR: An iterative method for solving sparse linear equations and sparse least squares problems.\n"
    "MINRES (Minimal Residual): Solves symmetric linear systems, particularly effective for symmetric indefinite systems.\n"
    "For a more detailed description, see the corresponding Internet resources."
)

HINT_CONFIG_THREAD_COUNT = "Thread count: Number of threads used for simulation. Range: 1 to the number of available threads on the system."
HINT_CONFIG_TIME_STEP = "Time Step: The time interval for each simulation step. Units: ns, μs, ms, s, min."
HINT_CONFIG_SIMULATION_TIME = "Simulation Time: Total time for the simulation. Units: ns, μs, ms, s, min."
HINT_CONFIG_TEMPERATURE = "Temperature: Initial temperature for the simulation. Units: K, F, C."
HINT_CONFIG_PRESSURE = "Pressure: Initial pressure for the simulation. Units: mPa, Pa, kPa, psi."

HINT_CONFIG_MESH_FILE = "Select the mesh file to use for the simulation. Supported formats: .msh, .stp, .vtk."
HINT_CONFIG_GAS_SELECTION = "Select the type of gas particles for the simulation. Options: O2, Ar, Ne, He."
HINT_CONFIG_SCATTERING_MODEL = "Select the scattering model to use in the simulation. Options: HS, VHS, VSS."

HINT_CONFIG_CUBIC_GRID_SIZE = (
    "Cubic Grid Size: This parameter specifies the edge size of the cubic cells in the 3D grid. "
    "The grid is used to map tetrahedrons to their containing cells, facilitating the determination of which tetrahedron contains a given particle. "
    "This grid-based approach improves the efficiency of spatial queries in the mesh.\n\n"
    f"If not specified - default value is {DEFAULT_CUBIC_GRID_SIZE}\n"
    f"Range: from {LIMIT_CONFIG_MIN_CUBIC_GRID_SIZE} to {LIMIT_CONFIG_MAX_CUBIC_GRID_SIZE}\n"
    "Purpose: The cubic grid helps in tracking particles within the volume by determining which tetrahedron each particle is located in. "
    "This is achieved by checking the intersection of particles with the cells of the grid and identifying the corresponding tetrahedrons.\n\n"
    "Warning: \n"
    f"- Setting the grid size too low (closer to {LIMIT_CONFIG_MIN_CUBIC_GRID_SIZE}) will result in a very fine grid, which may consume a significant amount of memory and can lead to performance issues.\n"
    f"- Setting the grid size too high (closer to {LIMIT_CONFIG_MAX_CUBIC_GRID_SIZE}) may result in an overly coarse grid, potentially causing incorrect determination of particle locations within the tetrahedrons."
)
HINT_CONFIG_FEM_ACCURACY = (
    "FEM Calculation Accuracy: This parameter determines the number of quadrature points used in the Finite Element Method (FEM) calculations, based on the desired accuracy. "
    "A higher accuracy typically requires more quadrature points, which increases both the computational cost and the memory usage of the program. "
    "However, it also improves the approximation of the integral.\n\n"
    "Purpose: The quadrature points are used to approximate integrals within the FEM. The more points used, the closer the numerical integration is to the actual value.\n\n"
    f"If not specified - default value is {DEFAULT_FEM_ACCURACY}\n"
    f"Range: from {LIMIT_CONFIG_MIN_FEM_ACCURACY} to {LIMIT_CONFIG_MAX_FEM_ACCURACY}\n"
    "Note: The specific number of quadrature points for a given accuracy is determined by an external library, Intrepid2.\n\n"
    "Warning: \n"
    f"- Lower accuracy settings (closer to {LIMIT_CONFIG_MIN_FEM_ACCURACY}) will reduce computational costs and memory usage, but may result in less accurate integral approximations."
    f"- Higher accuracy settings (closer to {LIMIT_CONFIG_MAX_FEM_ACCURACY}) will lead to increased computational costs and memory usage, but will provide better integral approximation.\n"
)

HINT_CONFIG_LOAD_MAGNETIC_INDUCTION = "Load Magnetic Induction: Load and parse the generated magnetic induction file from Ansys."
HINT_CONFIG_SELECT_BOUNDARY_CONDITIONS = "Select Boundary Conditions: Define the boundary conditions for the simulation."
