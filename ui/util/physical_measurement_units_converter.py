from constants import *
from util import *


class PhysicalMeasurementUnitsConverter:
    @staticmethod
    def to_kelvin(value, unit):
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)
        if unit == "K":
            return value
        elif unit == "F":
            return (value - 32.0) * (5.0 / 9.0) + 273.15
        elif unit == "C":
            return value + 273.15
        else:
            raise ValueError("Unsupported temperature unit")

    @staticmethod
    def to_seconds(value, unit):
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)
        unit_factors = {"ns": 1e-9, "μs": 1e-6,
                        "ms": 1e-3, "s": 1.0, "min": 60}
        return value * unit_factors.get(unit, 0)

    @staticmethod
    def to_pascal(value, unit):
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)
        unit_factors = {"mPa": 1e-3, "Pa": 1.0, "kPa": 1e3, "psi": 6894.76}
        return value * unit_factors.get(unit, 0)

    @staticmethod
    def to_cubic_meters(value, unit):
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)
        unit_factors = {"mm³": 1e-9, "cm³": 1e-6, "m³": 1.0}
        return value * unit_factors.get(unit, 0)

    @staticmethod
    def to_joules(value, unit):
        """
        Converts a given energy value from a specified unit to joules (J).

        Parameters:
        - value (str): The energy value to convert.
        - unit (str): The unit of the given value. Supported units: "eV", "keV", "J", "kJ", "cal".

        Returns:
        - float: The converted value in joules.
        """
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)

        # Conversion factors to joules
        unit_factors = {
            "eV": 1.602176634e-19,  # 1 eV to Joules
            "keV": 1.602176634e-16,  # 1 keV to Joules
            "J": 1.,                # 1 Joule to Joules
            "kJ": 1e3,              # 1 kilojoule to Joules
            "cal": 4.184,           # 1 calorie to Joules
        }

        # Default to 0 if unit is unsupported
        return value * unit_factors.get(unit, 0)
