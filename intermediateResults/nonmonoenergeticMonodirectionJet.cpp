#include <array>
#include <numbers>
#include <string>
#include <vector>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/MathVector.hpp"
#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"

template <typename T>
std::vector<T> createParticles(size_t count)
{
    RealNumberGenerator rng;
    std::vector<T> particles(count);

    double Vx{rng.get_double(1, 5)},
        Vy{rng.get_double(1, 5)},
        Vz{rng.get_double(1, 5)};
    for (size_t i{}; i < count; ++i)
    {
        double scalar{rng.get_double(1, 5)};
        std::cout << scalar << '\n';
        VelocityVector v(Vx, Vy, Vz);

        particles[i] = T(0, 0, 0,
                         v.getX() * scalar,
                         v.getY() * scalar,
                         v.getZ() * scalar);
    }
    return particles;
}

int main()
{
    TFile *file{new TFile("file.root", "recreate")};
    if (!file->IsOpen())
    {
        std::cout << std::format("Error: can't open file {}\n", file->GetName());
        return EXIT_FAILURE;
    }

    RealNumberGenerator rng;
    ParticlesAluminium p_Al(createParticles<ParticleAluminium>(1'000));
    ParticleArgon p_Ar;

    constexpr int frames{10};
    std::array<TH3D *, frames> snapshots;
    for (int i{}; i < frames; ++i)
        snapshots[i] = new TH3D(Form("volume_snapshot_%d", i), Form("Snapshot %d", i), 50, 0, 100, 50, 0, 100, 50, 0, 100);

    int snapshot_idx{};
    int time_interval(1'000), time_step(100), cur_time{}; // time in [ms]
    while (cur_time < time_interval)
    {
        for (size_t i{}; i < p_Al.size(); ++i)
            p_Al[i].updatePosition(time_step / 50);

        // Each 100-th iteration - snapshot
        if (cur_time % 100 == 0)
        {
            for (size_t i{}; i < p_Al.size(); ++i)
                snapshots[snapshot_idx]->Fill(p_Al[i].getX(), p_Al[i].getY(), p_Al[i].getZ());
            ++snapshot_idx;
        }

        cur_time += time_step;
    }

    for (int i{}; i < frames; ++i)
        snapshots[i]->Write();

    file->Close();

    return EXIT_SUCCESS;
}
