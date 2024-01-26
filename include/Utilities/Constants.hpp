#ifndef CONSTANTS_HPP
#define CONSTANTS_HPP

namespace constants
{
    namespace physical_constants
    {
        static constinit const double R{8.314};              // [J/k*mol]
        static constinit const double T{300};                // [k]
        static constinit const double N_av{6.22e23};         // Avogadro number
        static constinit const double eV_J{1.602176565e-19}; // Conversion factor of eV to J (1 eV is ...  J)
        static constinit const double J_eV{6.242e+18};       // Conversion factor of J to eV (1 J  is ... eV)

        /*** Weight of particles in [kg]. ***/
        static constinit const double Ar_mass{6.6335209e-26};
        static constinit const double N_mass{};
        static constinit const double He_mass{};
        static constinit const double Ti_mass{};
        static constinit const double Al_mass{4.4803831e-26};
        static constinit const double Sn_mass{};
        static constinit const double W_mass{};
        static constinit const double Au_mass{};
        static constinit const double Cu_mass{};
        static constinit const double Ni_mass{};
        static constinit const double Ag_mass{};

        /*** Radii of particles in [m]. ***/
        static constinit const double Ar_radius{98e-12};
        static constinit const double N_radius{};
        static constinit const double He_radius{};
        static constinit const double Ti_radius{};
        static constinit const double Al_radius{143e-12};
        static constinit const double Sn_radius{};
        static constinit const double W_radius{};
        static constinit const double Au_radius{};
        static constinit const double Cu_radius{};
        static constinit const double Ni_radius{};
        static constinit const double Ag_radius{};
    }

    namespace particle_types
    {
        enum ParticleType
        {
            Ar,
            N,
            He,
            Ti,
            Al,
            Sn,
            W,
            Au,
            Cu,
            Ni,
            Ag
        };
    }
}

#endif // !CONSTANTS_HPP
