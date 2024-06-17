from PyQt5.QtGui import QDoubleValidator


class CustomDoubleValidator(QDoubleValidator):
    def __init__(self, bottom, top, decimals, parent=None):
        super().__init__(bottom, top, decimals, parent)

    def validate(self, input_str, pos):
        if not input_str:
            return (self.Intermediate, input_str, pos)

        if '.' in input_str:
            try:
                value = float(input_str)
                if self.bottom() <= value <= self.top():
                    return (self.Acceptable, input_str, pos)
                else:
                    return (self.Invalid, input_str, pos)
            except ValueError:
                return (self.Invalid, input_str, pos)
        else:
            try:
                value = int(input_str)
                if self.bottom() <= value <= self.top():
                    return (self.Acceptable, input_str, pos)
                else:
                    return (self.Invalid, input_str, pos)
            except ValueError:
                return (self.Invalid, input_str, pos)

        return (self.Intermediate, input_str, pos)
