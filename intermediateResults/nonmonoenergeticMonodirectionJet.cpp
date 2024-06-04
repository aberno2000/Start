#include <array>
#include <numbers>
#include <source_location>
#include <string>
#include <vector>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/Geometry/MathVector.hpp"
#include "../include/Particles/Particle.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

int main()
{
    std::string root_file{std::source_location::current().file_name()};
    root_file.erase(root_file.find(".cpp"));
    root_file += ".root";

    TFile *file{new TFile(root_file.c_str(), "recreate")};
    if (!file->IsOpen())
    {
        std::cout << std::format("Error: can't open file {}\n", file->GetName());
        return EXIT_FAILURE;
    }

    RealNumberGenerator rng;
    ParticleVector p_Al(createParticlesWithEnergy(1'000, Al));
    Particle p_Ar(Ar, 0, 0, 0, 30);

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
