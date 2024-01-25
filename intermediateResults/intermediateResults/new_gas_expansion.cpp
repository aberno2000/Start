#include <array>
#include <numbers>
#include <string>
#include <vector>

#include <TBrowser.h>
#include <TFile.h>
#include <TH2D.h>
#include <TH3D.h>

#include "../include/Geometry/MathVector.hpp"
#include "../include/Particles/Particles.hpp"
#include "../include/Generators/RealNumberGenerator.hpp"

double get_normal(double mean, double sigma){
  RealNumberGenerator rng;
  double U1{rng()}, 
         U2{rng()};
  double z0 = sqrt(-2*std::log(U1))*cos(2*std::numbers::pi*U2);
  return mean + z0*sigma;

}

template <typename T>
std::vector<T> createParticles(size_t count)
{
    RealNumberGenerator rng;
    std::vector<T> particles(count);
    double calc_velocity = 2674;
    //double velocity = generateRandomNormal(calc_velocity, calc_velocity*0.2);
    for (size_t i{}; i < count; ++i)
        particles[i] = T(0.,0.,0.,0.,0., rng()*calc_velocity);
    return particles;
}


int main()
{
    double sigma = 4.5616710728287193e-20;
    double n_concentration = 3.7406783738272796e+20;

    ParticleAluminiumVector p_Al(createParticles<ParticleAluminium>(10'000'000));
    for(int i{0}; i<40; i++){
      
    p_Al[5].updatePosition(1E-6);
    //std::cout<<p_Al[5].getZ()<<"\n";
    }
   //std::cout<<p_Al[5].getZ()<<"\n";
    ParticleArgon p_Ar;

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

    for (int i{}; i < frames; ++i){
        snapshots[i] = new TH3D(Form("volume_snapshot_%d", i), Form("Snapshot %d", i), 150, 0, 0.2, 150, -0.1, 0.1, 150, -0.1, 0.1);
        z_distribution[i] = new TH1D(Form("Z hist_%d", i), Form("Z hist_%d", i),100, 0., 0.2 );
        hist_probability[i] = new TH1D(Form("probability_%d", i), Form("probability_%d", i),100, 0., 0.2 );

    }
    int snapshot_idx{};
    double time_interval = 100E-6;
    int total_frames = frames;
    double time_step = time_interval / total_frames;
    int snapshot_interval = total_frames / frames; // Calculate when to take snapshots evenly

    int snapshot_counter = 0;
    double cur_time = 0;

    while (cur_time < time_interval)
    {
        std::cout << "+\n";
        for (size_t i{}; i < p_Al.size(); ++i) {
            // std::cout << "Position:" << p_Al[5].getZ() << "\n"
            //           << "velocity:" << p_Al[5].getVz() << "\n";
            p_Al[i].updatePosition(time_step);
            
            double probability = sigma * p_Al[i].getVelocityModule()*n_concentration*time_step;
            //double probability=0.03;
            hist_probability[snapshot_counter]->Fill(probability);
//            std::cout << "probability:"<<probability<<"\n";
            if(probability<rng()) p_Al[i].colide( p_Al[0].getMass(),p_Ar.getMass());
        }

        // Take a snapshot when the counter reaches the interval
        if (snapshot_counter % snapshot_interval == 0) {
            for (size_t i{}; i < p_Al.size(); ++i){
                snapshots[snapshot_idx]->Fill(p_Al[i].getZ(), p_Al[i].getX(), p_Al[i].getY());
                z_distribution[snapshot_idx]->Fill(p_Al[i].getZ());    
            }
            std::cout << "Snapshot taken at time: " << cur_time << std::endl;
            snapshot_idx = (snapshot_idx + 1) % frames;

        }

        cur_time += time_step;
        ++snapshot_counter;
    }

   
    for (int i{}; i < frames; ++i){
        snapshots[i]->Write();
        z_distribution[i]->Write();
        hist_probability[i]->Write();
    }

//    TH2D* projection[3];
//    projection[0]=(TH2D*) snapshots[6]->Project3DProfile("ZX");
//    projection[0]->SetName("PZX");
//    projection[1]=(TH2D*) snapshots[6]->Project3DProfile("ZY");
//    projection[1]->SetName("PZY");
//    projection[2]=(TH2D*) snapshots[6]->Project3DProfile("XY");
//    projection[2]->SetName("PXY");
    
//    for(int i=0; i<3; i++) {
//      projection[i]->Write();
//    }
    file->Close();
}
//rotation is not working, but zapuskaetcya 
