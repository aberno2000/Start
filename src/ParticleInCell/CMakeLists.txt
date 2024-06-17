set(PIC_SOURCES
    Grid3D.cpp
    ParticleInCellTracker.cpp
)

add_library(ParticleInCell ${PIC_SOURCES})

target_link_libraries(ParticleInCell PRIVATE
    ${GMSH_LIBRARIES}
    ${CGAL_LIBRARIES}
    ${Boost_LIBRARIES}
    ${MPI_LIBRARIES}
    ${Trilinos_LIBRARIES}
)

target_include_directories(ParticleInCell PRIVATE
    ${CGAL_INCLUDE_DIRS}
    ${GMSH_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
    ${MPI_INCLUDE_PATH}
    ${Trilinos_INCLUDE_DIRS})
