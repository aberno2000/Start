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
template <typename T>
std::vector<T> createParticles(size_t count)
{
    RealNumberGenerator rng;
    std::vector<T> particles(count);
    for (size_t i{}; i < count; ++i)
        particles[i] = T(0.,0.,0.,rng(-1,1),rng(-1,1), rng(-1,1));
    return particles;
}


int main(){
  RealNumberGenerator rng;
  


  //ParticleAluminium p_Al(0.,0.,0.,-1.,1.,1.,0.2);
  ParticleAluminiumVector p_Al(createParticles<ParticleAluminium>(100));
  ParticleArgon p_Ar;
  for(auto& current: p_Al){
    current.updatePosition(5.);
    current.colide(rng(), current.getMass(), current.getMass()); 
  }
  return 0;
}
