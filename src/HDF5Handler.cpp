#include "../include/HDF5Handler.hpp"

HDF5Handler::HDF5Handler(std::string_view filename) : m_file_id(H5Fcreate(filename.data(),
                                                                          H5F_ACC_TRUNC,
                                                                          H5P_DEFAULT,
                                                                          H5P_DEFAULT)) {}

HDF5Handler::~HDF5Handler() { H5Fclose(m_file_id); }

void HDF5Handler::saveMeshToHDF5(TriangleMeshParams const &triangles)
{
    for (auto const &triangle : triangles)
    {
        auto id{std::get<0>(triangle)};

        // Create a group for each triangle using the triangle ID as the group name
        hid_t grp_id{H5Gcreate2(m_file_id, ("Triangle_" + std::to_string(id)).c_str(),
                                H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};

        // Store data related to the triangle in the group
        double coordinates[9] = {
            std::get<1>(triangle).getX(), std::get<1>(triangle).getY(), std::get<1>(triangle).getZ(),
            std::get<2>(triangle).getX(), std::get<2>(triangle).getY(), std::get<2>(triangle).getZ(),
            std::get<3>(triangle).getX(), std::get<3>(triangle).getY(), std::get<3>(triangle).getZ()};

        hsize_t dims[1] = {9};
        hid_t dataspace{H5Screate_simple(1, dims, NULL)},
            dataset{H5Dcreate2(grp_id, "Coordinates", H5T_NATIVE_DOUBLE, dataspace,
                               H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT)};
        H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates);
        H5Dclose(dataset);
        H5Sclose(dataspace);

        double area{std::get<4>(triangle)};
        dataspace = H5Screate(H5S_SCALAR);
        dataset = H5Dcreate2(grp_id, "Area", H5T_NATIVE_DOUBLE, dataspace,
                             H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        H5Dwrite(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(area));
        H5Dclose(dataset);
        H5Sclose(dataspace);

        dataspace = H5Screate(H5S_SCALAR);
        dataset = H5Dcreate2(grp_id, "Counter", H5T_NATIVE_INT, dataspace,
                             H5P_DEFAULT, H5P_DEFAULT, H5P_DEFAULT);
        int zeroBuf{};
        H5Dwrite(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(zeroBuf));
        H5Dclose(dataset);
        H5Sclose(dataspace);

        H5Gclose(grp_id);
    }
}

TriangleMeshParams HDF5Handler::readMeshFromHDF5()
{
    TriangleMeshParams mesh;

    hid_t grp_id{}, dataset_id{};
    hsize_t num_objs{};
    H5Gget_num_objs(m_file_id, std::addressof(num_objs));

    for (hsize_t i{}; i < num_objs; ++i)
    {
        grp_id = H5Gopen2(m_file_id, std::to_string(i).c_str(), H5P_DEFAULT);

        double coordinates[9]{};
        dataset_id = H5Dopen2(grp_id, "Coordinates", H5P_DEFAULT);
        H5Dread(dataset_id, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, coordinates);
        H5Dclose(dataset_id);

        double area{};
        dataset_id = H5Dopen2(grp_id, "Area", H5P_DEFAULT);
        H5Dread(dataset_id, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(area));
        H5Dclose(dataset_id);

        int counter{};
        dataset_id = H5Dopen2(grp_id, "Counter", H5P_DEFAULT);
        H5Dread(dataset_id, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, std::addressof(counter));
        H5Dclose(dataset_id);

        mesh.emplace_back(std::make_tuple(i, PositionVector{coordinates[0], coordinates[1], coordinates[2]},
                                          PositionVector{coordinates[3], coordinates[4], coordinates[5]},
                                          PositionVector{coordinates[6], coordinates[7], coordinates[8]},
                                          area, counter));

        H5Gclose(grp_id);
    }

    return mesh;
}
