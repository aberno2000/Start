from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QVBoxLayout, QMessageBox
from converter import is_positive_real_number, is_real_number

class PointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Create Point")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for input fields
        formLayout = QFormLayout()
        
        # Input fields for the sphere parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        
        layout.addLayout(formLayout)
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):        
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        return float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text())


class LineDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Line")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        # Input fields for the start point
        self.x1Input = QLineEdit("0.0")
        self.y1Input = QLineEdit("0.0")
        self.z1Input = QLineEdit("0.0")
        
        # Input fields for the end point
        self.x2Input = QLineEdit("0.0")
        self.y2Input = QLineEdit("0.0")
        self.z2Input = QLineEdit("0.0")
        
        formLayout.addRow("Start X:", self.x1Input)
        formLayout.addRow("Start Y:", self.y1Input)
        formLayout.addRow("Start Z:", self.z1Input)
        formLayout.addRow("End X:", self.x2Input)
        formLayout.addRow("End Y:", self.y2Input)
        formLayout.addRow("End Z:", self.z2Input)
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)

    def getValues(self):
        if not all(is_real_number(value.text()) for value in [self.x1Input, self.y1Input, self.z1Input, self.x2Input, self.y2Input, self.z2Input]):
            QMessageBox.warning(self, "Invalid input", "All coordinates must be real numbers.")
            return None
        return tuple(float(field.text()) for field in [self.x1Input, self.y1Input, self.z1Input, self.x2Input, self.y2Input, self.z2Input])


class SurfaceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Surface")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        # Input fields for three points
        self.inputs = [QLineEdit("0.0") for _ in range(9)]  # x1, y1, z1, x2, y2, z2, x3, y3, z3
        
        for i, point in enumerate(['Point 1', 'Point 2', 'Point 3']):
            formLayout.addRow(f"{point} X:", self.inputs[i*3])
            formLayout.addRow(f"{point} Y:", self.inputs[i*3+1])
            formLayout.addRow(f"{point} Z:", self.inputs[i*3+2])
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        if not all(is_real_number(input_field.text()) for input_field in self.inputs):
            QMessageBox.warning(self, "Invalid input", "All coordinates must be real numbers.")
            return None
        return tuple(float(field.text()) for field in self.inputs)


class SphereDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Create Sphere")
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create form layout for input fields
        formLayout = QFormLayout()
        
        # Input fields for the sphere parameters
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.radiusInput = QLineEdit("5.0")
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Radius:", self.radiusInput)
        
        layout.addLayout(formLayout)
        
        # Dialog buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
        
    def getValues(self):        
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_positive_real_number(self.radiusInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.radiusInput.text()} isn't a real positive number")
            return None
        return float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()), float(self.radiusInput.text())


class BoxDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Box")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.lengthInput = QLineEdit("5.0")
        self.widthInput = QLineEdit("5.0")
        self.heightInput = QLineEdit("5.0")
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Length:", self.lengthInput)
        formLayout.addRow("Width:", self.widthInput)
        formLayout.addRow("Height:", self.heightInput)
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_positive_real_number(self.lengthInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.lengthInput.text()} isn't a real positive number")
            return None
        if not is_positive_real_number(self.widthInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.widthInput.text()} isn't a real positive number")
            return None
        if not is_positive_real_number(self.heightInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.heightInput.text()} isn't a real positive number")
            return None
        return (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                float(self.lengthInput.text()), float(self.widthInput.text()), float(self.heightInput.text()))


class CylinderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Cylinder")
        
        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        
        self.xInput = QLineEdit("0.0")
        self.yInput = QLineEdit("0.0")
        self.zInput = QLineEdit("0.0")
        self.radiusInput = QLineEdit("2.5")
        self.heightInput = QLineEdit("5.0")
        
        formLayout.addRow("Center X:", self.xInput)
        formLayout.addRow("Center Y:", self.yInput)
        formLayout.addRow("Center Z:", self.zInput)
        formLayout.addRow("Radius:", self.radiusInput)
        formLayout.addRow("Height:", self.heightInput)
        
        layout.addLayout(formLayout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.buttons)
    
    def getValues(self):
        if not is_real_number(self.xInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.xInput.text()} isn't a real number")
            return None
        if not is_real_number(self.yInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.yInput.text()} isn't a real number")
            return None
        if not is_real_number(self.zInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.zInput.text()} isn't a real number")
            return None
        if not is_positive_real_number(self.radiusInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.radiusInput.text()} isn't a real positive number")
            return None
        if not is_positive_real_number(self.heightInput.text()):
            QMessageBox.warning(self, "Invalid input", f"{self.heightInput.text()} isn't a real positive number")
            return None
        return (float(self.xInput.text()), float(self.yInput.text()), float(self.zInput.text()),
                float(self.radiusInput.text()), float(self.heightInput.text()))

