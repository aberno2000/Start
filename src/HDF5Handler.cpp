#include <stdexcept>

#include "../include/HDF5Handler.hpp"

HDF5Handler::HDF5Handler(std::string_view filename) : m_file_id(H5Fcreate(filename.data(),
                                                                          H5F_ACC_TRUNC,
                                                                          H5P_DEFAULT,
                                                                          H5P_DEFAULT)) {}

HDF5Handler::~HDF5Handler() { H5Fclose(m_file_id); }

void HDF5Handler::updateParticleCounters(std::unordered_map<size_t, int> const &triangleCounters)
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
    if (triangles.empty())
        return;
    m_firstTriangleID = std::get<0>(triangles[0]);

    for (auto const &triangle : triangles)
    {
        // Creating a group for each triangle using the triangle ID as the group name
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        hid_t grp_id{H5Gcreate2(m_file_id, groupName.c_str(), H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
        if (grp_id < 0)
            throw std::runtime_error("Failed to create group: " + groupName);

        // Store data related to the triangle in the group
        double coordinates[9] = {
            std::get<1>(triangle).getX(), std::get<1>(triangle).getY(), std::get<1>(triangle).getZ(),
            std::get<2>(triangle).getX(), std::get<2>(triangle).getY(), std::get<2>(triangle).getZ(),
            std::get<3>(triangle).getX(), std::get<3>(triangle).getY(), std::get<3>(triangle).getZ()};

        hsize_t dims[1] = {9};
        hid_t dataspace{H5Screate_simple(1, dims, NULL)},
            dataset{H5Dcreate2(grp_id, "Coordinates", H5T_NATIVE_DOUBLE, dataspace,
                               H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
        if (dataspace < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace 'Coordinates' in group: " + groupName);
        }
        if (dataset < 0)
        {
            H5Dclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataset 'Coordinates' in group: " + groupName);
        }
        H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates);
        H5Dclose(dataset);
        H5Sclose(dataspace);

        double area{std::get<4>(triangle)};
        dataspace = H5Screate(H5S_SCALAR);
        if (dataspace < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace 'Area' in group: " + groupName);
        }
        dataset = H5Dcreate2(grp_id, "Area", H5T_NATIVE_DOUBLE, dataspace,
                             H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Dclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataset 'Area' in group: " + groupName);
        }
        H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(area));
        H5Dclose(dataset);
        H5Sclose(dataspace);

        dataspace = H5Screate(H5S_SCALAR);
        if (dataspace < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataspace 'Counter' in group: " + groupName);
        }
        dataset = H5Dcreate2(grp_id, "Counter", H5T_NATIVE_INT, dataspace,
                             H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Dclose(dataspace);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to create dataset 'Counter' in group: " + groupName);
        }
        int count{};
        if (H5Dwrite(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(count)) < 0)
        {
            H5Dclose(dataset);
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to write to dataset 'Counter' in group: " + groupName);
        }
        H5Dclose(dataset);
        H5Sclose(dataspace);

        H5Gclose(grp_id);
    }
}

TriangleMeshParamVector HDF5Handler::readMeshFromHDF5()
{
    TriangleMeshParamVector mesh;

    hid_t grp_id{}, dataset{};
    hsize_t num_objs{};
    H5Gget_num_objs(m_file_id, std::addressof(num_objs));

    for (hsize_t i{m_firstTriangleID}; i < num_objs; ++i)
    {
        std::string groupName("Triangle_" + std::to_string(i));
        grp_id = H5Gopen2(m_file_id, groupName.c_str(), H5P_DEFAULT);
        if (grp_id < 0)
            throw std::runtime_error("Failed to open group: " + groupName);

        double coordinates[9]{};
        dataset = H5Dopen2(grp_id, "Coordinates", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Coordinates' in group: " + groupName);
        }
        H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates);
        H5Dclose(dataset);

        double area{};
        dataset = H5Dopen2(grp_id, "Area", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Area' in group: " + groupName);
        }
        H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(area));
        H5Dclose(dataset);

        int count{};
        dataset = H5Dopen2(grp_id, "Counter", H5P_DEFAULT);
        if (dataset < 0)
        {
            H5Gclose(grp_id);
            throw std::runtime_error("Failed to open dataset 'Counter' in group: " + groupName);
        }
        H5Dread(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(count));
        H5Dclose(dataset);

        mesh.emplace_back(std::make_tuple(i, PositionVector{coordinates[0], coordinates[1], coordinates[2]},
                                          PositionVector{coordinates[3], coordinates[4], coordinates[5]},
                                          PositionVector{coordinates[6], coordinates[7], coordinates[8]},
                                          area, count));

        H5Gclose(grp_id);
    }

    return mesh;
}
