#ifndef PARTICLETRACKER_HPP
#define PARTICLETRACKER_HPP

#include <mutex>
#include <set>

#include "FiniteElementMethod/MatrixEquationSolver.hpp"
#include "Generators/VolumeCreator.hpp"
#include "Geometry/Mesh.hpp"
#include "ParticleInCell/Grid3D.hpp"
#include "Particles/Particles.hpp"

class ParticleTracker final
{
    using NodeTetrahedronMap = std::map<size_t, std::vector<std::size_t>>;
    using BoundaryNodes = std::vector<size_t>;

private:
    /* All neccessary data members from the mesh. */
    std::string m_mesh_filename;                 ///< Mesh filename (must has .msh format).
    MeshTriangleParamVector _triangleMesh;       ///< Triangle mesh params acquired from the mesh file. Surface mesh.
    TriangleVector _triangles;                   ///< Triangles extracted from the triangle mesh params `_triangleMesh` (surface mesh). Need to initialize AABB tree.
    AABB_Tree_Triangle _surfaceMeshAABBtree;     ///< AABB tree for the surface mesh to effectively detect collisions with surface.
    MeshTetrahedronParamVector _tetrahedronMesh; ///< Tetrahedron mesh params acquired from the mesh file. Volume mesh.
    NodeTetrahedronMap _nodeTetraMap;            ///< Map for the nodes and tetrahedrons - which tetrahedrons surround certain node. (Node ID | Tetrahedron IDs).
    BoundaryNodes _boundaryNodes;                ///< Vector of the boundary nodes (All of them are unique).
    GMSHVolumeCreator vc;                        ///< Object of the volume creator that is RAII object that initializes and finalizes GMSH. Needed to initialize all necessary objects from the mesh.

    /* All neccessary data members for the FEM. */
    static constexpr short const kdefault_polynomOrder{1}; ///< Polynom order. Responds for count of the basis functions.
    short _desiredAccuracy{3};                             ///<  Desired accuracy of calculations (responds for the count of cubature points (Trilinos automatically chose them)).

    /* All neccessary data members for the simulation. */
    ParticleVector m_particles;         ///< Projective particles.
    std::set<int> _settledParticlesIds; ///< Set of the particle IDs that are been settled (need to avoid checking already settled particles).

    /**
     * @brief Checks the validity of the provided mesh filename.
     *
     * This function performs several checks to ensure that the provided mesh filename
     * is valid and can be opened. It checks if the filename is empty, if the file exists,
     * and if the file has the correct `.msh` extension. If any of these conditions are not met,
     * an error message is logged and a `std::runtime_error` is thrown.
     *
     * @param mesh_filename The filename of the mesh to be checked.
     * @throws std::runtime_error if the filename is empty, if the file does not exist, or if the file does not have a `.msh` extension.
     */
    void checkMeshfilename(std::string_view mesh_filename) const;

    /* Initializers for all the necessary objects. */
    void initializeSurfaceMesh();
    void initializeSurfaceMeshAABB();
    void initializeVolumeMesh();
    void initializeNodeTetrahedronMap();
    void initializeBoundaryNodes();
    void initializeParticles(ParticleType const &particleType, size_t count);

    /// @brief Global initializator. Uses all the initializers above.
    void initialize();

    /**
     * @brief Checker for point inside the tetrahedron.
     * @param point `Point_3` from CGAL.
     * @param tetrahedron `Tetrahedron_3` from CGAL.
     * @return `true` if point within the tetrahedron, otherwise `false`.
     */
    bool isPointInsideTetrahedron(Point const &point, MeshTetrahedronParam const &meshParam);

    /**
     * @brief Checker for ray-triangle intersection.
     * @param ray Finite ray object - line segment.
     * @param triangle Triangle object.
     * @return ID with what triangle ray intersects, otherwise max `size_t` value (-1ul).
     */
    size_t isRayIntersectTriangle(Ray const &ray, MeshTriangleParam const &triangle);

public:
    ParticleTracker(std::string_view mesh_filename);
    void startSimulation(ParticleType const &particleType, size_t count, double edgeSize,
                         short desiredAccuracy, double time_step, double simulation_time);
};

#endif // !PARTICLETRACKER_HPP
