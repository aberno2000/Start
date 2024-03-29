#include <filesystem>
#include <stdexcept>

#include "../include/DataHandling/HDF5Handler.hpp"

HDF5Handler::HDF5Handler(std::string_view filename)
{
    if (std::filesystem::exists(filename))
        std::filesystem::remove(filename);

    m_file_id = H5Fcreate(filename.data(), H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (m_file_id < 0)
        throw std::runtime_error("Failed to create HDF5 file: " + std::string(filename));
}

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

void HDF5Handler::saveMeshToHDF5(MeshTriangleParamVector const &mesh)
{
    if (mesh.empty())
        return;

    auto minTriangle{*std::min_element(mesh.cbegin(), mesh.cend(),
                                       [](MeshTriangleParam const &a, MeshTriangleParam const &b)
                                       { return std::get<0>(a) < std::get<0>(b); })};
    m_firstID = std::get<0>(minTriangle);

    for (auto const &triangle : mesh)
    {
        // Creating a group for each triangle using the triangle ID as the group name
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        createGroup(groupName);

        // Store data related to the triangle in the group
        double coordinates[9] = {
            CGAL::to_double(std::get<1>(triangle).vertex(0).x()), CGAL::to_double(std::get<1>(triangle).vertex(0).y()), CGAL::to_double(std::get<1>(triangle).vertex(0).z()),
            CGAL::to_double(std::get<1>(triangle).vertex(1).x()), CGAL::to_double(std::get<1>(triangle).vertex(1).y()), CGAL::to_double(std::get<1>(triangle).vertex(1).z()),
            CGAL::to_double(std::get<1>(triangle).vertex(2).x()), CGAL::to_double(std::get<1>(triangle).vertex(2).y()), CGAL::to_double(std::get<1>(triangle).vertex(2).z())};
        writeDataset(groupName, "Coordinates", H5T_NATIVE_DOUBLE, coordinates, 9);

        double area{std::get<2>(triangle)};
        writeDataset(groupName, "Area", H5T_NATIVE_DOUBLE, std::addressof(area), 1);

        int count{std::get<3>(triangle)};
        writeDataset(groupName, "Counter", H5T_NATIVE_INT, std::addressof(count), 1);
    }
}

void HDF5Handler::saveMeshToHDF5(MeshTriangleParamVector &&mesh)
{
    if (mesh.empty())
        return;

    auto minTriangle{*std::min_element(mesh.cbegin(), mesh.cend(),
                                       [](MeshTriangleParam const &a, MeshTriangleParam const &b)
                                       { return std::get<0>(a) < std::get<0>(b); })};
    m_firstID = std::get<0>(minTriangle);

    for (auto const &triangle : mesh)
    {
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        createGroup(groupName);

        double coordinates[9] = {
            CGAL::to_double(std::get<1>(triangle).vertex(0).x()), CGAL::to_double(std::get<1>(triangle).vertex(0).y()), CGAL::to_double(std::get<1>(triangle).vertex(0).z()),
            CGAL::to_double(std::get<1>(triangle).vertex(1).x()), CGAL::to_double(std::get<1>(triangle).vertex(1).y()), CGAL::to_double(std::get<1>(triangle).vertex(1).z()),
            CGAL::to_double(std::get<1>(triangle).vertex(2).x()), CGAL::to_double(std::get<1>(triangle).vertex(2).y()), CGAL::to_double(std::get<1>(triangle).vertex(2).z())};
        writeDataset(groupName, "Coordinates", H5T_NATIVE_DOUBLE, coordinates, 9);

        double area{std::get<2>(triangle)};
        writeDataset(groupName, "Area", H5T_NATIVE_DOUBLE, std::addressof(area), 1);

        int count{std::get<3>(triangle)};
        writeDataset(groupName, "Counter", H5T_NATIVE_INT, std::addressof(count), 1);
    }
}

MeshTriangleParamVector HDF5Handler::readMeshFromHDF5()
{
    MeshTriangleParamVector mesh;
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
        Triangle tmp(Point(coordinates[0], coordinates[1], coordinates[2]),
                      Point(coordinates[3], coordinates[4], coordinates[5]),
                      Point(coordinates[6], coordinates[7], coordinates[8]));
        mesh.emplace_back(std::make_tuple(id, tmp, area, counter));
    }

    return mesh;
}
