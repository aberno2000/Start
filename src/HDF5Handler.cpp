#include <stdexcept>

#include "../include/HDF5Handler.hpp"

HDF5Handler::HDF5Handler(std::string_view filename) : m_file_id(H5Fcreate(filename.data(),
                                                                          H5F_ACC_TRUNC,
                                                                          H5P_DEFAULT,
                                                                          H5P_DEFAULT)) {}

HDF5Handler::~HDF5Handler() { H5Fclose(m_file_id); }

void HDF5Handler::updateParticleCounters(std::unordered_map<unsigned long, int> const &triangleCounters)
{
    for (auto const &[id, count] : triangleCounters)
    {
        std::string groupName("Triangle_" + std::to_string(id));
        hid_t grp_id{H5Gopen2(m_file_id, groupName.c_str(), H5P_DEFAULT)};
        if (grp_id < 0)
            throw std::runtime_error("Failed to open group: " + groupName);

        hid_t dataset{H5Dopen2(grp_id, "Counter", H5P_DEFAULT)};
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Counter' in group: " + groupName);
        }

        if (H5Dwrite(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(count)) < 0)
        {
            H5Dclose(dataset);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to write to dataset 'Counter' in group: " + groupName);
        }

        H5Dclose(dataset);
        H5Gclose(grp_id);
    }
}

void HDF5Handler::saveMeshToHDF5(TriangleMeshParamVector const &triangles)
{
    for (auto const &triangle : triangles)
    {
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        hid_t grp_id{H5Gcreate2(m_file_id, groupName.c_str(), H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
        if (grp_id < 0)
        {
            throw std::runtime_error("Failed to create group: " + groupName);
        }

        double coordinates[9] = {
            std::get<1>(triangle).getX(), std::get<1>(triangle).getY(), std::get<1>(triangle).getZ(),
            std::get<2>(triangle).getX(), std::get<2>(triangle).getY(), std::get<2>(triangle).getZ(),
            std::get<3>(triangle).getX(), std::get<3>(triangle).getY(), std::get<3>(triangle).getZ()};

        hsize_t dims[1] = {9};
        hid_t dataspace{H5Screate_simple(1, dims, nullptr)},
            dataset{H5Dcreate2(grp_id, "Coordinates", H5T_NATIVE_DOUBLE, dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
        if (dataspace < 0 || dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace or dataset 'Coordinates' in group: " + groupName);
        }
        if (H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates) < 0)
        {
            H5Dclose(dataset);
            H5Sclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to write to dataset 'Coordinates' in group: " + groupName);
        }
        H5Dclose(dataset);
        H5Sclose(dataspace);

        double area{std::get<4>(triangle)};
        dataspace = H5Screate(H5S_SCALAR);
        dataset = H5Dcreate2(grp_id, "Area", H5T_NATIVE_DOUBLE, dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        if (dataspace < 0 || dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace or dataset 'Area' in group: " + groupName);
        }
        if (H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &area) < 0)
        {
            H5Dclose(dataset);
            H5Sclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to write to dataset 'Area' in group: " + groupName);
        }
        H5Dclose(dataset);
        H5Sclose(dataspace);

        int count{};
        dataspace = H5Screate(H5S_SCALAR);
        dataset = H5Dcreate2(grp_id, "Counter", H5T_NATIVE_INT, dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        if (dataspace < 0 || dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace or dataset 'Counter' in group: " + groupName);
        }
        if (H5Dwrite(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &count) < 0)
        {
            H5Dclose(dataset);
            H5Sclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to write to dataset 'Counter' in group: " + groupName);
        }
        H5Dclose(dataset);
        H5Sclose(dataspace);
        H5Gclose(grp_id);
    }
}

inline TriangleMeshParamVector HDF5Handler::readMeshFromHDF5(size_t firstObjectID)
{
    TriangleMeshParamVector mesh;

    hid_t grp_id{}, dataset{};
    hsize_t num_objs{};
    if (H5Gget_num_objs(m_file_id, &num_objs) < 0)
    {
        throw std::runtime_error("Failed to get the number of objects in the HDF5 file.");
    }

    for (hsize_t i{firstObjectID}; i < num_objs; ++i)
    {
        std::string groupName("Triangle_" + std::to_string(i));
        grp_id = H5Gopen2(m_file_id, groupName.c_str(), H5P_DEFAULT);
        if (grp_id < 0)
        {
            throw std::runtime_error("Failed to open group: " + groupName);
        }

        double coordinates[9]{};
        dataset = H5Dopen2(grp_id, "Coordinates", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Coordinates' in group: " + groupName);
        }
        if (H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates) < 0)
        {
            H5Dclose(dataset);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to read dataset 'Coordinates' in group: " + groupName);
        }
        H5Dclose(dataset);

        double area{};
        dataset = H5Dopen2(grp_id, "Area", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Area' in group: " + groupName);
        }
        if (H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &area) < 0)
        {
            H5Dclose(dataset);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to read dataset 'Area' in group: " + groupName);
        }
        H5Dclose(dataset);

        int count{};
        dataset = H5Dopen2(grp_id, "Counter", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Counter' in group: " + groupName);
        }
        if (H5Dread(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &count) < 0)
        {
            H5Dclose(dataset);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to read dataset 'Counter' in group: " + groupName);
        }
        H5Dclose(dataset);
        H5Gclose(grp_id);
    }

    return mesh;
}
