def is_real_number(value: str):
    try:
        float(value)
        return True
    except ValueError:
        return False
    

def is_positive_real_number(value: str):
    try:
        float(value)
        if float(value) < 0:
            return False
        return True
    except ValueError:
        return False


class Converter:
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
        unit_factors = {"ns": 1e-9, "μs": 1e-6, "ms": 1e-3, "s": 1.0, "min": 60}
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
    def to_electron_volts(value, unit):
        if not is_positive_real_number(value):
            return 0.0
        value = float(value)
        unit_factors = {"J": 6.2415093433e18, "eV": 1.0}
        return value * unit_factors.get(unit, 0)
