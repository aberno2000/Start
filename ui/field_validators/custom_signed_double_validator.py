from PyQt5.QtGui import QDoubleValidator
from re import match

class CustomSignedDoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.decimals = decimals

    def validate(self, input_str, pos):
        # Replace comma with dot for uniform interpretation
        input_str = input_str.replace(',', '.')

        # Allow empty input
        if not input_str:
            return self.Intermediate, input_str, pos

        # Allow '-' if it's the first character
        if input_str == '-':
            return self.Intermediate, input_str, pos

        # Generate regex pattern for intermediate values based on decimals
        intermediate_pattern = f"^-?0(\\.0{{0,{self.decimals}}})?$"
        complete_pattern = f"^-?\\d*\\.?\\d{{0,{self.decimals}}}$"

        if match(intermediate_pattern, input_str):
            return self.Intermediate, input_str, pos

        if match(complete_pattern, input_str):
            try:
                value = float(input_str)
                if self.bottom() <= value <= self.top():
                    return self.Acceptable, input_str, pos
                else:
                    return self.Invalid, input_str, pos
            except ValueError:
                return self.Invalid, input_str, pos

        return self.Invalid, input_str, pos
