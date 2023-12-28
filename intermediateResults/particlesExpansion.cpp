#include <array>
#include <numbers>
#include <string>
#include <vector>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/Particle.hpp"
#include "../include/RealNumberGenerator.hpp"

template <typename T>
std::vector<T> createParticles(size_t count)
{
    RealNumberGenerator rng;
    std::vector<T> particles(count);

    for (size_t i{}; i < count; ++i)
        particles[i] = T(50,                    // x
                         50,                    // y
                         50,                    // z
                         rng.get_double(0, 2),  // Vx
                         rng.get_double(0, 2),  // Vy
                         rng.get_double(0, 2)); // Vz
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
    ParticlesAluminium p_Al(createParticles<ParticleAluminium>(10000));
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
        {
            p_Al[i].updatePosition(time_step / 50);
            if (rng() < 0.5)
                p_Al[i].colide(rng.get_double(0, std::numbers::pi), rng.get_double(0, 2 * std::numbers::pi),
                               p_Al[0].getMass(), p_Ar.getMass());
        }

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
