#include <cmath>
#include <format>
#include <iostream>
#include <numbers>
#include <tuple>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/RealNumberGenerator.hpp"
#include "../include/Timer.hpp"

void GenerateConeWithNumbers()
{
  TFile *file{new TFile("file.root", "recreate")};
  if (!file->IsOpen())
  {
    std::cout << std::format("Error: can't open file {}\n", file->GetName());
    return;
  }

  TH2D *plane{new TH2D("plane", "plane", 50, -1, 1, 50, -1, 1)};
  TH3D *volume{new TH3D("volume", "volume", 50, -1, 1, 50, -1, 1, 50, 0, 1)};

  RealNumberGenerator rng;
  for (auto [v_mod, phi, vx, vy, vz, theta, i]{std::tuple{0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0}};
       i < 1'000'000;
       ++i, v_mod = rng(),
            phi = rng.get_double(0, 2) * std::numbers::pi,
            theta = rng() * (1.0 / 6.0) * std::numbers::pi)
  {
    vx = v_mod * sin(theta) * cos(phi),
    vy = v_mod * sin(theta) * sin(phi),
    vz = v_mod * cos(theta);

    plane->Fill(vx, vy);
    volume->Fill(vx, vy, vz);
  }

  plane->Write();
  volume->Write();
  file->Close();
}

int main()
{
  GenerateConeWithNumbers();
  return EXIT_SUCCESS;
}
