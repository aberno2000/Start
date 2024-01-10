template <SphereConcept T>
std::vector<int> VolumeCreator::createSpheres(std::span<T const> spheres)
{
    std::vector<int> dimTags;
    for (auto const &sphere : spheres)
        dimTags.emplace_back(createSphere(std::get<0>(sphere),
                                          std::get<1>(sphere),
                                          std::get<2>(sphere),
                                          std::get<3>(sphere)));
    return dimTags;
}
