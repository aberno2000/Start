from re import split
from constants import *

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


def is_positive_natural_number(value: str):
    try:
        num = int(value)
        return num > 0
    except ValueError:
        return False


def is_mesh_dims(value: str):
    try:
        num = int(value)
        return num > 0 and num < 4
    except ValueError:
        return False


def ansi_to_segments(text: str):
    segments = []
    current_color = 'light gray'  # Default color
    buffer = ""

    def append_segment(text, color):
        if text:  # Only append non-empty segments
            segments.append((text, color))

    # Split the text by ANSI escape codes
    parts = split(r'(\033\[\d+(?:;\d+)*m)', text)
    for part in parts:
        if not part:  # Skip empty strings
            continue
        if part.startswith('\033['):
            # Remove leading '\033[' and trailing 'm', then split
            codes = part[2:-1].split(';')
            for code in codes:
                if code in ANSI_TO_QCOLOR:
                    current_color = ANSI_TO_QCOLOR[code]
                    # Append the current buffer with the current color
                    append_segment(buffer, current_color)
                    buffer = ""  # Reset buffer
                    break  # Only apply the first matching color
        else:
            buffer += part  # Add text to the buffer
    append_segment(buffer, current_color)  # Append any remaining text
    return segments


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
