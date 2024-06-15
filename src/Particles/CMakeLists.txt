set(PARTICLES_SOURCES
    Particle.cpp
)

add_library(Particles ${PARTICLES_SOURCES})

target_link_libraries(Particles PRIVATE
    ${Boost_LIBRARIES}
    Generators
)

target_include_directories(Particles PRIVATE
    ${Boost_INCLUDE_DIRS})
