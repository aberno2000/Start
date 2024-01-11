#ifndef HDF5HANDLER_HPP
#define HDF5HANDLER_HPP

#include <hdf5.h>
#include <string_view>

#include "Mesh.hpp"

class HDF5Handler final
{
private:
    hid_t m_file_id;

public:
    explicit HDF5Handler(std::string_view filename);
    ~HDF5Handler();

    // !Maybe useless method!
    // void saveParticlesToHDF5(ParticleVector const &particles);

    void saveMeshToHDF5(TriangleMeshParams const &triangles);
    TriangleMeshParams readMeshFromHDF5();
};

// Count of settled particles on certain triangle
// `key` is the id of the certain triangle
// `value` is the count of settled particles
// std::unordered_map<int, int> settledCount;

#endif // !HDF5HANDLER_HPP
