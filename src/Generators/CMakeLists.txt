set(GENERATORS_SOURCES
    RealNumberGenerator.cpp
    VolumeCreator.cpp
)

add_library(Generators ${GENERATORS_SOURCES})

target_link_libraries(Generators PRIVATE
    ${Boost_LIBRARIES}
)

target_include_directories(Generators PRIVATE
    ${Boost_INCLUDE_DIRS})
