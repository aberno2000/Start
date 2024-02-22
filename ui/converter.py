from re import compile, split

ANSI_COLOR_REGEX = compile(r'\033\[(\d+)(;\d+)*m')
ANSI_TO_QCOLOR = {
    '0': ('light gray', False),  # Reset to default
    '1': ('', True),             # Bold text
    '4': ('', True),             # Underline
    '30': 'black',
    '31': 'red',
    '32': 'green',
    '33': 'yellow',
    '34': 'blue',
    '35': 'magenta',
    '36': 'cyan',
    '37': 'white',
}

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


def ansi_to_segments(text: str):
    segments = []
    current_color = 'light gray'  # Default color
    is_bold = False  # Track if bold text is needed
    buffer = ""

    # Function to append text segments
    def append_segment(text, color):
        if text:  # Only append non-empty segments
            segments.append((text.strip() + '\n', color))

    # Split the text by ANSI escape codes
    parts = split(r'(\033\[\d+(?:;\d+)*m)', text)
    for part in parts:
        if not part:  # Skip empty strings
            continue
        # Check if the part is an ANSI escape code
        if part.startswith('\033['):
            codes = part[2:-1].split(';')  # Remove leading '\033[' and trailing 'm', then split
            for code in codes:
                if code in ANSI_TO_QCOLOR:
                    color_info = ANSI_TO_QCOLOR[code]
                    if isinstance(color_info, tuple):
                        color, is_bold = color_info
                        if not color:  # If no color change, keep current color
                            continue
                    else:
                        color = color_info
                    append_segment(buffer, current_color)  # Append the current buffer with the current color
                    buffer = ""  # Reset buffer
                    current_color = color  # Update current color
                    break  # Only apply the first matching color
        else:
            buffer += part  # Add text to the buffer
    append_segment(buffer, current_color)  # Append any remaining text
    return segments

def insert_segments_into_log_console(segments, logConsole):
    for text, color in segments:
        logConsole.insert_colored_text(text, color)

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
            "keV": 1.602176634e-16, # 1 keV to Joules
            "J": 1.,                # 1 Joule to Joules
            "kJ": 1e3,              # 1 kilojoule to Joules
            "cal": 4.184,           # 1 calorie to Joules
        }
        
        return value * unit_factors.get(unit, 0)  # Default to 0 if unit is unsupported

