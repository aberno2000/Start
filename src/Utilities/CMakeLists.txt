set(UTILITIES_SOURCES
    CollisionTracker.cpp
    ConfigParser.cpp
    Timer.cpp
    Utilities.cpp
)

add_library(Utilities ${UTILITIES_SOURCES})

target_link_libraries(Utilities PRIVATE
    ${Boost_LIBRARIES}
    ${TBB_LIBRARIES}
)

target_include_directories(Utilities PRIVATE
    ${Boost_INCLUDE_DIRS}
    ${TBB_INCLUDE_DIRS})
