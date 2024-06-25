from PyQt5.QtGui import QDoubleValidator


class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)
        self.decimals = decimals

    def validate(self, input_str, pos):
        # Replace comma with dot for uniform interpretation
        input_str = input_str.replace(',', '.')

        # Allow empty input initially
        if not input_str:
            return self.Intermediate, input_str, pos

        # Check if the input string is a valid number
        try:
            value = float(input_str)
            # Allow zero value regardless of format
            if value == 0:
                return self.Acceptable, input_str, pos
            # Check if the value is within the valid range
            if self.bottom() <= value <= self.top():
                parts = input_str.split('.')
                if len(parts) == 2 and len(parts[1]) <= self.decimals:
                    return self.Acceptable, input_str, pos
                elif len(parts) == 1:
                    return self.Acceptable, input_str, pos
            return self.Invalid, input_str, pos
        except ValueError:
            # Allow intermediate state for partial inputs
            return self.Intermediate, input_str, pos
