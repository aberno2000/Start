#include <array>
#include <string>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/Generators/RealNumberGenerator.hpp"
#include "../include/Particles/Particles.hpp"

#define N 1'000'000

int main()
{
    // data anfd generation
    //
    double sigma{4.5616710728287193e-20}, n_concentration{2.4937855825515197e+20};
    Particle p_Ar(Ar, 0, 0, 0, 500, 500, 500);
    ParticleVector p_Al(createParticlesWithVelocities(N, Al, 0, 0, 0, 0, 0, 0, 0,
                                                      0, 0, 0, 0, 2649));
    for (int i{}; i < N; i++)
        p_Al[i].updatePosition(1e-6);

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

    constexpr int frames{10};
    std::array<TH3D *, frames> snapshots;
    std::array<TH1D *, frames> z_distribution;
    std::array<TH1D *, frames> hist_probability;

    for (int i{}; i < frames; ++i)
    {
        snapshots[i] =
            new TH3D(Form("volume_snapshot_%d", i), Form("Snapshot %d", i), 150, 0,
                     0.2, 150, -0.1, 0.1, 150, -0.1, 0.1);
        z_distribution[i] =
            new TH1D(Form("Z hist_%d", i), Form("Z hist_%d", i), 100, 0., 0.2);
        hist_probability[i] = new TH1D(Form("probability_%d", i),
                                       Form("probability_%d", i), 100, 0., 0.2);
    }

    // beguining of
    int snapshot_idx{}, snapshot_counter{};
    double time_interval{50E-6},
        time_step{time_interval / frames},
        cur_time{};

    while (cur_time < time_interval)
    {
        std::cout << "+\n";
        for (size_t i{}; i < p_Al.size(); ++i)
        {
            p_Al[i].updatePosition(time_step);
            double probability{sigma * p_Al[i].getVelocityModule() * n_concentration * time_step};
            hist_probability[snapshot_counter]->Fill(probability);
            if (probability < rng())
                p_Al[i].colide(p_Al[0].getMass(), p_Ar.getMass());
        }

        // Take a snapshot when the counter reaches the interval
        for (size_t i{}; i < p_Al.size(); ++i)
        {
            snapshots[snapshot_idx]->Fill(p_Al[i].getZ(), p_Al[i].getX(), p_Al[i].getY());
            z_distribution[snapshot_idx]->Fill(p_Al[i].getZ());
        }
        std::cout << "Snapshot taken at time: " << cur_time << std::endl;
        snapshot_idx = (snapshot_idx + 1) % frames;

        cur_time += time_step;
        ++snapshot_counter;
    }

    for (int i{}; i < frames; ++i)
    {
        snapshots[i]->Write();
        z_distribution[i]->Write();
        hist_probability[i]->Write();
    }
    file->Close();
}
