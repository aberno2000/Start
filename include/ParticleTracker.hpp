#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <barrier>
#include <mutex>

#include "FiniteElementMethod/MatrixEquationSolver.hpp"
#include "Generators/VolumeCreator.hpp"
#include "Geometry/Mesh.hpp"
#include "ParticleInCell/Grid3D.hpp"
#include "Particles/Particles.hpp"
#include "Utilities/ConfigParser.hpp"

class ParticleTracker final
{
private:
    static constexpr short const kdefault_polynomOrder{1}; ///< Polynom order. Responds for count of the basis functions.

    std::once_flag m_solve_once_flag;               ///< Matrix equation must be solved only one time.
    static std::mutex m_PICTracker_mutex;           ///< Mutex for synchronizing access to the particles in tetrahedrons.
    static std::mutex m_nodeChargeDensityMap_mutex; ///< Mutex for synchronizing access to the charge densities in nodes.
    static std::mutex m_particlesMovement_mutex;    ///< Mutex for synchronizing access to particle movements.
    static std::mutex m_settledParticles_mutex;     ///< Mutex for synchronizing access to settled particle IDs.
    static std::atomic_flag m_stop_processing;      ///< Flag-checker for condition (counter >= size of particles).

    /* All the neccessary data members from the mesh. */
    MeshTriangleParamVector _triangleMesh;   ///< Triangle mesh params acquired from the mesh file. Surface mesh.
    TriangleVector _triangles;               ///< Triangles extracted from the triangle mesh params `_triangleMesh` (surface mesh). Need to initialize AABB tree.
    AABB_Tree_Triangle _surfaceMeshAABBtree; ///< AABB tree for the surface mesh to effectively detect collisions with surface.
    GMSHVolumeCreator vc;                    ///< Object of the volume creator that is RAII object that initializes and finalizes GMSH. Needed to initialize all necessary objects from the mesh.

    /* All the neccessary data members for the simulation. */
    ParticleVector m_particles;                        ///< Projective particles.
    double _gasConcentration;                          ///< Gas concentration. Needed to use colide projectives with gas mechanism.
    std::set<int> _settledParticlesIds;                ///< Set of the particle IDs that are been settled (need to avoid checking already settled particles).
    std::map<size_t, int> _settledParticlesCounterMap; ///< Map to handle settled particles: (Triangle ID | Counter of settled particle in this triangle).

    ConfigParser m_config;                                    ///< `ConfigParser` object to get all the simulation physical paramters.
    std::map<size_t, std::vector<Point>> m_particlesMovement; ///< Map to store all the particle movements: (Particle ID | All positions).

    /**
     * @brief Checks the validity of the provided mesh filename.
     *
     * This function performs several checks to ensure that the provided mesh filename
     * is valid and can be opened. It checks if the filename is empty, if the file exists,
     * and if the file has the correct `.msh` extension. If any of these conditions are not met,
     * an error message is logged and a `std::runtime_error` is thrown.
     *
     * @throws std::runtime_error if the filename is empty, if the file does not exist, or if the file does not have a `.msh` extension.
     */
    void checkMeshfilename() const;

    /* Initializers for all the necessary objects. */
    void initializeSurfaceMesh();
    void initializeSurfaceMeshAABB();
    void initializeParticles();

    /// @brief Global initializator. Uses all the initializers above.
    void initialize();

    /// @brief Clears out all the files that are generated from the UI side of the application.
    void finalize() const { saveParticleMovements(); }

    /**
     * @brief Saves the particle movements to a JSON file.
     *
     * This function saves the contents of m_particlesMovement to a JSON file named "particles_movements.json".
     * It handles exceptions and provides a warning message if the map is empty.
     */
    void saveParticleMovements() const;

    /**
     * @brief Checker for point inside the tetrahedron.
     * @param point `Point_3` from CGAL.
     * @param tetrahedron `Tetrahedron_3` from CGAL.
     * @return `true` if point within the tetrahedron, otherwise `false`.
     */
    bool isPointInsideTetrahedron(Point const &point, Tetrahedron const &tetrahedron);

    /**
     * @brief Checker for ray-triangle intersection.
     * @param ray Finite ray object - line segment.
     * @param triangle Triangle object.
     * @return ID with what triangle ray intersects, otherwise max `size_t` value (-1ul).
     */
    size_t isRayIntersectTriangle(Ray const &ray, MeshTriangleParam const &triangle);

    /// @brief Using HDF5Handler to update the mesh according to the settled particles.
    void updateSurfaceMesh();

    void processPIC(size_t start_index, size_t end_index,
                    Grid3D const &cubicGrid, GSMatrixAssemblier &assemblier,
                    std::map<size_t, ParticleVector> &globalPICtracker,
                    std::map<GlobalOrdinal, double> &nodeChargeDensityMap);
    void solveEquation(std::map<GlobalOrdinal, double> &nodeChargeDensityMap,
                       GSMatrixAssemblier &assemblier, SolutionVector &solutionVector,
                       std::map<GlobalOrdinal, double> &boundaryConditions, double time);
    void processSurfaceCollisionTracker(size_t start_index, size_t end_index,
                                        Grid3D const &cubicGrid, GSMatrixAssemblier const &assemblier,
                                        std::map<size_t, ParticleVector> const &PICtracker);

    /**
     * @brief Processes a segment of the particle collection to detect collisions.
     *
     * @details This method runs in multiple threads, each processing a specified range of particles.
     *          It updates particle positions and detects collisions with mesh elements,
     *          recording collision counts.
     *
     * @param start_index The starting index in the particle vector for this segment.
     * @param end_index The ending index in the particle vector for this segment.
     * TODO:
     */
    void processSegment(size_t start_index, size_t end_index,
                        Grid3D const &cubicGrid, GSMatrixAssemblier &assemblier, SolutionVector &solutionVector,
                        std::map<GlobalOrdinal, double> &boundaryConditions, std::map<GlobalOrdinal, double> &nodeChargeDensityMap,
                        std::barrier<> &barrier);

public:
    ParticleTracker(std::string_view config_filename);
    ~ParticleTracker() { finalize(); }

    void startSimulation();
};

#endif // !PARTICLETRACKER_HPP
