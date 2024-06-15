set(DATA_HANDLING_SOURCES
    HDF5Handler.cpp
    VolumetricMeshData.cpp
)

add_library(DataHandling ${DATA_HANDLING_SOURCES})

target_link_libraries(DataHandling PRIVATE
    ${HDF5_LIBRARIES}
)

target_include_directories(DataHandling PRIVATE
    ${HDF5_INCLUDE_DIRS})
