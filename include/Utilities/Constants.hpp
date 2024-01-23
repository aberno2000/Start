#ifndef CONSTANTS_HPP
#define CONSTANTS_HPP

namespace physical_constants
{
    static constexpr const double R{8.314};              // [J/k*mol]
    static constexpr const double T{300};                // [k]
    static constexpr const double N_av{6.22e23};         // Avogadro number
    static constexpr const double eV_J{1.602176565e-19}; // Conversion factor of eV to J (1 eV is ...  J)
    static constexpr const double J_eV{6.242e+18};       // Conversion factor of J to eV (1 J  is ... eV)

    /*** Weight of particles in [kg]. ***/
    static constexpr const double AlMass{4.4803831e-26};
    static constexpr const double ArMass{6.6335209e-26};

    /*** Radii of particles in [m]. ***/
    static constexpr const double AlRadius{143e-12};
    static constexpr const double ArRadius{98e-12};
}

#endif // !CONSTANTS_HPP
