#include <stdexcept>

#include "../include/HDF5Handler.hpp"

HDF5Handler::HDF5Handler(std::string_view filename) : m_file_id(H5Fcreate(filename.data(),
                                                                          H5F_ACC_TRUNC,
                                                                          H5P_DEFAULT,
                                                                          H5P_DEFAULT)) {}

HDF5Handler::~HDF5Handler() { H5Fclose(m_file_id); }

void HDF5Handler::createGroup(std::string_view groupName)
{
    hid_t grp_id{H5Gcreate2(m_file_id, groupName.data(), H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
    if (grp_id < 0)
        throw std::runtime_error("Failed to create group: " + std::string(groupName));
    H5Gclose(grp_id);
}

void HDF5Handler::writeDataset(std::string_view groupName, std::string_view datasetName,
                               hid_t type, void const *data, hsize_t dims)
{
    hid_t grp_id{H5Gopen2(m_file_id, groupName.data(), H5P_DEFAULT)},
        dataspace{H5Screate_simple(1, std::addressof(dims), NULL)},
        dataset{H5Dcreate2(grp_id, datasetName.data(), type, dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
    if (dataspace < 0 || dataset < 0)
    {
        H5Gclose(grp_id);
        throw std::runtime_error("Failed to create dataset " + std::string(datasetName) + " in group: " + std::string(groupName));
    }
    H5Dwrite(dataset, type, H5S_ALL, H5S_ALL, H5P_DEFAULT, data);
    H5Dclose(dataset);
    H5Sclose(dataspace);
    H5Gclose(grp_id);
}

void HDF5Handler::readDataset(std::string_view groupName, std::string_view datasetName,
                              hid_t type, void *data)
{
    hid_t grp_id{H5Gopen2(m_file_id, groupName.data(), H5P_DEFAULT)},
        dataset{H5Dopen2(grp_id, datasetName.data(), H5P_DEFAULT)};
    if (dataset < 0)
    {
        H5Gclose(grp_id);
        throw std::runtime_error("Failed to open dataset " + std::string(datasetName) + " in group: " + std::string(groupName));
    }
    H5Dread(dataset, type, H5S_ALL, H5S_ALL, H5P_DEFAULT, data);
    H5Dclose(dataset);
    H5Gclose(grp_id);
}

void HDF5Handler::saveMeshToHDF5(TriangleMeshParamVector const &mesh)
{
    if (mesh.empty())
        return;

    auto minIDIter{
        std::min_element(mesh.cbegin(), mesh.cend(),
                         [](TriangleMeshParam const &a, TriangleMeshParam const &b)
                         { return std::get<0>(a) < std::get<0>(b); })};
    auto minTriangle{*minIDIter};
    m_firstID = std::get<0>(minTriangle);

    for (auto const &triangle : mesh)
    {
        // Creating a group for each triangle using the triangle ID as the group name
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        createGroup(groupName);

        // Store data related to the triangle in the group
        double coordinates[9] = {
            std::get<1>(triangle).getX(), std::get<1>(triangle).getY(), std::get<1>(triangle).getZ(),
            std::get<2>(triangle).getX(), std::get<2>(triangle).getY(), std::get<2>(triangle).getZ(),
            std::get<3>(triangle).getX(), std::get<3>(triangle).getY(), std::get<3>(triangle).getZ()};
        writeDataset(groupName, "Coordinates", H5T_NATIVE_DOUBLE, coordinates, 9);

        double area{std::get<4>(triangle)};
        writeDataset(groupName, "Area", H5T_NATIVE_DOUBLE, std::addressof(area), 1);

        int count{std::get<5>(triangle)};
        writeDataset(groupName, "Counter", H5T_NATIVE_INT, std::addressof(count), 1);
    }
}

TriangleMeshParamVector HDF5Handler::readMeshFromHDF5()
{
    TriangleMeshParamVector mesh;
    hsize_t num_objs{};
    H5Gget_num_objs(m_file_id, std::addressof(num_objs));
    m_lastID = m_firstID + num_objs;

    for (size_t id{m_firstID}; id < m_lastID; ++id)
    {
        std::string groupName("Triangle_" + std::to_string(id));

        double coordinates[9]{};
        readDataset(groupName, "Coordinates", H5T_NATIVE_DOUBLE, coordinates);

        double area{};
        readDataset(groupName, "Area", H5T_NATIVE_DOUBLE, std::addressof(area));

        int counter{};
        readDataset(groupName, "Counter", H5T_NATIVE_INT, std::addressof(counter));

        // Construct the tuple and add to the mesh vector
        PositionVector vertex1(coordinates[0], coordinates[1], coordinates[2]),
            vertex2(coordinates[3], coordinates[4], coordinates[5]),
            vertex3(coordinates[6], coordinates[7], coordinates[8]);
        mesh.emplace_back(std::make_tuple(id, vertex1, vertex2, vertex3, area, counter));
    }

    return mesh;
}
