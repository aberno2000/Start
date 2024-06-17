set(GEOMETRY_SOURCES
    MathVector.cpp
    Mesh.cpp
    RayTriangleIntersection.cpp
)

add_library(Geometry ${GEOMETRY_SOURCES})

target_link_libraries(Geometry PRIVATE
    ${GMSH_LIBRARIES}
    ${CGAL_LIBRARIES}
)

target_include_directories(Geometry PRIVATE
    ${CGAL_INCLUDE_DIRS}
    ${GMSH_INCLUDE_DIRS})
