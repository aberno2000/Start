#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <mutex>
#include <set>

#include "FiniteElementMethod/MatrixEquationSolver.hpp"
#include "Generators/VolumeCreator.hpp"
#include "Geometry/Mesh.hpp"
#include "ParticleInCell/Grid3D.hpp"
#include "Particles/Particles.hpp"
#include "Utilities/ConfigParser.hpp"

static constexpr std::string_view const kdefault_temp_picfem_params_filename{"temp_picfem_params.json"};
static constexpr std::string_view const kdefault_temp_solver_params_filename{"temp_solver_params.json"};
static constexpr std::string_view const kdefault_temp_boundary_conditions_filename{"temp_boundary_conditions.json"};

class ParticleTracker final
{
    using NodeTetrahedronMap = std::map<size_t, std::vector<std::size_t>>;
    using BoundaryNodes = std::vector<size_t>;

private:
    /* All the neccessary data members from the mesh. */
    MeshTriangleParamVector _triangleMesh;   ///< Triangle mesh params acquired from the mesh file. Surface mesh.
    TriangleVector _triangles;               ///< Triangles extracted from the triangle mesh params `_triangleMesh` (surface mesh). Need to initialize AABB tree.
    AABB_Tree_Triangle _surfaceMeshAABBtree; ///< AABB tree for the surface mesh to effectively detect collisions with surface.
    BoundaryNodes _boundaryNodes;            ///< Vector of the boundary nodes (All of them are unique).
    GMSHVolumeCreator vc;                    ///< Object of the volume creator that is RAII object that initializes and finalizes GMSH. Needed to initialize all necessary objects from the mesh.

    /* All the neccessary data members for the PIC and FEM. */
    static constexpr short const kdefault_polynomOrder{1}; ///< Polynom order. Responds for count of the basis functions.
    util::PICFEMParameters _picfemparams;                  ///< Contains cubic 3D grid edge size as `.first` data member and desired calculation accuracy as `.second` data member.
    util::BoundaryConditionsData _boundaryConditions;      ///< Boundary conditions data storage.

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
    void initializeBoundaryNodes();
    void loadPICFEMParameters();
    void loadBoundaryConditions();
    void initializeParticles();

    /// @brief Global initializator. Uses all the initializers above.
    void initialize();

    /// @brief Clears out all the files that are generated from the UI side of the application.
    void finalize() const;

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

    /// @brief Removes all the temporary files from system.
    void removeTemporaryFiles() const;

    /**
     * @brief Saves the particle movements to a JSON file.
     *
     * This function saves the contents of m_particlesMovement to a JSON file named "particles_movements.json".
     * It handles exceptions and provides a warning message if the map is empty.
     */
    void saveParticleMovements() const;

    /// @brief Using HDF5Handler to update the mesh according to the settled particles.
    void updateSurfaceMesh();

    void processSegment();

public:
    ParticleTracker(std::string_view config_filename);
    ~ParticleTracker() { finalize(); }

    void startSimulation();
};

#endif // !PARTICLETRACKER_HPP
