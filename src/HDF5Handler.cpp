#include <stdexcept>

#include "../include/HDF5Handler.hpp"

HDF5Resource::HDF5Resource(hid_t resource) : m_resource(resource) {}

HDF5Resource::~HDF5Resource()
{
    if (m_resource >= 0)
        H5Dclose(m_resource);
}

HDF5Resource::HDF5Resource(HDF5Resource &&other) noexcept : m_resource(other.m_resource)
{
    other.m_resource = -1; // Invalidate the old resource handle.
}

HDF5Resource &HDF5Resource::operator=(HDF5Resource &&other) noexcept
{
    if (this != std::addressof(other))
    {
        close();                       // Close existing resource.
        m_resource = other.m_resource; // Transfer ownership.
        other.m_resource = -1;         // Invalidate the old resource handle.
    }
    return *this;
}

hid_t HDF5Resource::get() const { return m_resource; }

void HDF5Resource::close()
{
    if (m_resource >= 0)
    {
        H5Dclose(m_resource);
        m_resource = -1;
    }
}

hid_t HDF5Handler::openGroup(std::string_view groupName) const
{
    hid_t grp_id{H5Gopen2(m_file_id, groupName.data(), H5P_DEFAULT)};
    if (grp_id < 0)
        throw std::runtime_error("Failed to open group: " + std::string(groupName));
    return grp_id;
}

hid_t HDF5Handler::createDataSet(hid_t grp_id, std::string_view dataSetName, hid_t dataType, hsize_t *dims, int rank) const
{
    hid_t dataspace{H5Screate_simple(rank, dims, nullptr)};
    hid_t dataset{H5Dcreate2(grp_id, dataSetName.data(), dataType, dataspace, H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
    H5Sclose(dataspace);
    if (dataset < 0)
        throw std::runtime_error("Failed to create dataset '" + std::string(dataSetName) + "'");
    return dataset;
}

void HDF5Handler::writeDataSet(hid_t dataset, hid_t dataType, void const *data, std::string_view dataSetName) const
{
    if (H5Dwrite(dataset, dataType, H5S_ALL, H5S_ALL, H5P_DEFAULT, data) < 0)
        throw std::runtime_error("Failed to write to dataset '" + std::string(dataSetName) + "'");
}

void HDF5Handler::readDataSet(hid_t dataset, hid_t dataType, void *data, std::string_view dataSetName) const
{
    if (H5Dread(dataset, dataType, H5S_ALL, H5S_ALL, H5P_DEFAULT, data) < 0)
        throw std::runtime_error("Failed to read dataset '" + std::string(dataSetName) + "'");
}

void HDF5Handler::closeHDF5Resource(hid_t resource) const
{
    if (resource >= 0)
        H5Dclose(resource);
}

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
        HDF5Resource grp_id{openGroup(groupName)};
        HDF5Resource dataset{HDF5Resource{H5Dopen2(grp_id.get(), "Counter", H5P_DEFAULT)}};

        if (dataset.get() < 0)
            throw std::runtime_error("Failed to open dataset 'Counter' in group: " + groupName);

        writeDataSet(dataset.get(), H5T_NATIVE_INT, &count, "Counter");
    }
}

void HDF5Handler::saveMeshToHDF5(TriangleMeshParamVector const &triangles)
{
    for (auto const &triangle : triangles)
    {
        auto id{std::get<0>(triangle)};
        std::string groupName("Triangle_" + std::to_string(id));
        HDF5Resource grp_id{HDF5Resource{H5Gcreate2(m_file_id, groupName.c_str(), H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)}};

        if (grp_id.get() < 0)
            throw std::runtime_error("Failed to create group: " + groupName);

        double coordinates[9] = {
            std::get<1>(triangle).getX(), std::get<1>(triangle).getY(), std::get<1>(triangle).getZ(),
            std::get<2>(triangle).getX(), std::get<2>(triangle).getY(), std::get<2>(triangle).getZ(),
            std::get<3>(triangle).getX(), std::get<3>(triangle).getY(), std::get<3>(triangle).getZ()};
        hsize_t dims[1] = {9};
        HDF5Resource dataset{createDataSet(grp_id.get(), "Coordinates", H5T_NATIVE_DOUBLE, dims, 1)};
        writeDataSet(dataset.get(), H5T_NATIVE_DOUBLE, coordinates, "Coordinates");

        double area{std::get<4>(triangle)};
        HDF5Resource area_dataset{createDataSet(grp_id.get(), "Area", H5T_NATIVE_DOUBLE, nullptr, 0)};
        writeDataSet(area_dataset.get(), H5T_NATIVE_DOUBLE, std::addressof(area), "Area");

        int count{};
        HDF5Resource counter_dataset{createDataSet(grp_id.get(), "Counter", H5T_NATIVE_INT, nullptr, 0)};
        writeDataSet(counter_dataset.get(), H5T_NATIVE_INT, std::addressof(count), "Counter");
    }
}

inline TriangleMeshParamVector HDF5Handler::readMeshFromHDF5()
{
    TriangleMeshParamVector mesh;

    hsize_t num_objs{};
    if (H5Gget_num_objs(m_file_id, std::addressof(num_objs)) < 0)
        throw std::runtime_error("Failed to get the number of objects in the HDF5 file.");

    for (hsize_t i{0}; i < num_objs; ++i)
    {
        std::string groupName("Triangle_" + std::to_string(i));
        HDF5Resource grp_id{openGroup(groupName)};

        double coordinates[9]{};
        HDF5Resource dataset = HDF5Resource{H5Dopen2(grp_id.get(), "Coordinates", H5P_DEFAULT)};
        if (dataset.get() < 0)
            throw std::runtime_error("Failed to open dataset 'Coordinates' in group: " + groupName);
        readDataSet(dataset.get(), H5T_NATIVE_DOUBLE, coordinates, "Coordinates");

        double area{};
        HDF5Resource area_dataset = HDF5Resource{H5Dopen2(grp_id.get(), "Area", H5P_DEFAULT)};
        if (area_dataset.get() < 0)
            throw std::runtime_error("Failed to open dataset 'Area' in group: " + groupName);
        readDataSet(area_dataset.get(), H5T_NATIVE_DOUBLE, std::addressof(area), "Area");

        int count{};
        HDF5Resource counter_dataset = HDF5Resource{H5Dopen2(grp_id.get(), "Counter", H5P_DEFAULT)};
        if (counter_dataset.get() < 0)
            throw std::runtime_error("Failed to open dataset 'Counter' in group: " + groupName);
        readDataSet(counter_dataset.get(), H5T_NATIVE_INT, std::addressof(count), "Counter");

        mesh.emplace_back(std::make_tuple(i, PositionVector{coordinates[0], coordinates[1], coordinates[2]},
                                          PositionVector{coordinates[3], coordinates[4], coordinates[5]},
                                          PositionVector{coordinates[6], coordinates[7], coordinates[8]},
                                          area, count));
    }

    return mesh;
}
