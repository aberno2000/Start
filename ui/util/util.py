from vtk import vtkRenderer
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from styles import *
from constants import *


def get_cur_datetime() -> str:
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_thread_count():
    from multiprocessing import cpu_count
    return cpu_count()


def get_os_info():
    from platform import platform
    return platform()


def rad_to_degree(angle: float):
    from math import pi
    return angle * 180. / pi


def degree_to_rad(angle: float):
    from math import pi
    return angle * pi / 180.


def is_mesh_dims(value: str):
    try:
        num = int(value)
        return num > 0 and num < 4
    except ValueError:
        return False


def ansi_to_segments(text: str):
    from re import split
    
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


def align_view_by_axis(axis: str, renderer: vtkRenderer,
                       vtkWidget: QVTKRenderWindowInteractor):
    axis = axis.strip().lower()

    if axis not in ['x', 'y', 'z', 'center']:
        return

    camera = renderer.GetActiveCamera()
    if axis == 'x':
        camera.SetPosition(1, 0, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'y':
        camera.SetPosition(0, 1, 0)
        camera.SetViewUp(0, 0, 1)
    elif axis == 'z':
        camera.SetPosition(0, 0, 1)
        camera.SetViewUp(0, 1, 0)
    elif axis == 'center':
        camera.SetPosition(1, 1, 1)
        camera.SetViewUp(0, 0, 1)

    camera.SetFocalPoint(0, 0, 0)

    renderer.ResetCamera()
    vtkWidget.GetRenderWindow().Render()


def calculate_direction(base, tip):
    from numpy import array, linalg

    base = array(base)
    tip = array(tip)

    direction = tip - base

    norm = linalg.norm(direction)
    if norm == 0:
        raise ValueError("The direction vector cannot be zero.")
    direction /= norm

    return direction


def calculate_thetaPhi(base, tip):
    from numpy import arctan2, arccos

    direction = calculate_direction(base, tip)
    x, y, z = direction[0], direction[1], direction[2]

    theta = arccos(z)
    phi = arctan2(y, x)

    return theta, phi


def calculate_thetaPhi_with_angles(x, y, z, angle_x, angle_y, angle_z):
    from numpy import array, cos, sin, arccos, arctan2, linalg, radians
    
    direction_vector = array([
        cos(radians(angle_y)) * cos(radians(angle_z)),
        sin(radians(angle_x)) * sin(radians(angle_z)),
        cos(radians(angle_x)) * cos(radians(angle_y))
    ])
    norm = linalg.norm(direction_vector)
    theta = arccos(direction_vector[2] / norm)
    phi = arctan2(direction_vector[1], direction_vector[0])
    return theta, phi


def compute_distance_between_points(coord1, coord2):
    """
    Compute the Euclidean distance between two points in 3D space.
    """
    from math import sqrt
    from logger import InternalLogger
    
    try:
        result = sqrt((coord1[0] - coord2[0])**2 +
                      (coord1[1] - coord2[1])**2 +
                      (coord1[2] - coord2[2])**2)
    except Exception as e:
        print(InternalLogger.get_warning_none_result_with_exception_msg(e))
        return None
    return result
