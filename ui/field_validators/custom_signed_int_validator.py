from PyQt5.QtGui import QIntValidator


class CustomSignedIntValidator(QIntValidator):

    def __init__(self, bottom, top, parent=None):
        super().__init__(bottom, top, parent)

    def validate(self, input_str, pos):
        # Allow empty input
        if not input_str:
            return (self.Intermediate, input_str, pos)

        # Allow '-' if it's the first character
        if input_str == '-':
            return (self.Intermediate, input_str, pos)

        try:
            value = int(input_str)
            if self.bottom() <= value <= self.top():
                return (self.Acceptable, input_str, pos)
            else:
                return (self.Invalid, input_str, pos)
        except ValueError:
            return (self.Invalid, input_str, pos)

        return (self.Intermediate, input_str, pos)
