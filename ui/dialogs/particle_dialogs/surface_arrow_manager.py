from PyQt5.QtWidgets import QMessageBox
from vtk import (
    vtkActor, vtkRenderer, vtkPolyDataNormals, vtkMath,
    vtkArrowSource, vtkTransform, vtkTransformPolyDataFilter,
    vtkPolyDataMapper
)
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from logger.log_console import LogConsole
from styles import *
from constants import *
from .particle_source_dialog import ParticleSourceDialog
from .normal_orientation_dialog import NormalOrientationDialog


class SurfaceArrowManager:
    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, 
                 renderer: vtkRenderer, 
                 log_console: LogConsole, 
                 selected_actors: set, 
                 particle_source_manager, 
                 geditor):
        self.vtkWidget = vtkWidget
        self.renderer = renderer
        self.log_console = log_console
        self.selected_actors = selected_actors
        self.arrow_size = DEFAULT_ARROW_SCALE[0]
        self.selected_actor = None
        self.particle_source_manager = particle_source_manager
        self.geditor = geditor

    def render_editor_window(self):
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def set_particle_source_as_surface(self):
        if not self.selected_actors:
            self.log_console.printWarning("There is no selected surfaces to apply particle source on them")
            QMessageBox.information(self.geditor, "Set Particle Source", "There is no selected surfaces to apply particle source on them")
            return

        self.selected_actor = list(self.selected_actors)[0]
        self.select_surface_and_normals(self.selected_actor)
        if not self.selected_actor:
            return

        self.particle_source_dialog = ParticleSourceDialog(self.geditor)
        self.particle_source_dialog.accepted_signal.connect(lambda params: self.handle_particle_source_surface_accepted(params, self.data))

    def handle_particle_source_surface_accepted(self, particle_params, surface_and_normals_dict):
        try:
            particle_type = particle_params["particle_type"]
            energy = particle_params["energy"]
            num_particles = particle_params["num_particles"]

            self.log_console.printInfo("Particle source set as surface source\n"
                                       f"Particle Type: {particle_type}\n"
                                       f"Energy: {energy} eV\n"
                                       f"Number of Particles: {num_particles}")
            self.log_console.addNewLine()

            self.particle_source_manager.update_config_with_particle_source(particle_params, surface_and_normals_dict)
        except Exception as e:
            self.log_console.printError(f"Error setting particle source. {e}")
            QMessageBox.warning(self.geditor, "Particle Source", f"Error setting particle source. {e}")
            return None

    def add_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.AddActor(arrow_actor)
        self.render_editor_window()

    def remove_arrows(self, arrows):
        for arrow_actor, _, _ in arrows:
            self.renderer.RemoveActor(arrow_actor)
        self.render_editor_window()

    def update_arrow_sizes(self, size):
        for arrow_actor, cell_center, normal in self.arrows_outside:
            self.renderer.RemoveActor(arrow_actor)
        for arrow_actor, cell_center, normal in self.arrows_inside:
            self.renderer.RemoveActor(arrow_actor)

        self.arrows_outside = [
            (self.create_arrow_actor(cell_center, normal, size), cell_center, normal)
            for _, cell_center, normal in self.arrows_outside
        ]
        self.arrows_inside = [
            (self.create_arrow_actor(cell_center, normal, size), cell_center, normal)
            for _, cell_center, normal in self.arrows_inside
        ]

        self.add_arrows(self.arrows_outside)

    def populate_data(self, arrows, data):
        for arrow_actor, cell_center, normal in arrows:
            actor_address = hex(id(arrow_actor))
            data[actor_address] = {
                "cell_center": cell_center, "normal": normal}

    def select_surface_and_normals(self, actor: vtkActor):
        poly_data = actor.GetMapper().GetInput()
        normals = self.calculate_normals(poly_data)

        if not normals:
            self.log_console.printWarning(
                "No normals found for the selected surface")
            QMessageBox.warning(self.geditor, "Normals Calculation",
                                "No normals found for the selected surface")
            return

        self.num_cells = poly_data.GetNumberOfCells()
        self.arrows_outside = []
        self.arrows_inside = []
        self.data = {}

        for i in range(self.num_cells):
            normal = normals.GetTuple(i)
            rev_normal = tuple(-n if n != 0 else 0.0 for n in normal)
            cell = poly_data.GetCell(i)
            cell_center = self.calculate_cell_center(cell)

            arrow_outside = self.create_arrow_actor(
                cell_center, normal, self.arrow_size)
            arrow_inside = self.create_arrow_actor(
                cell_center, rev_normal, self.arrow_size)

            self.arrows_outside.append((arrow_outside, cell_center, normal))
            self.arrows_inside.append((arrow_inside, cell_center, rev_normal))
        self.add_arrows(self.arrows_outside)

        self.normal_orientation_dialog = NormalOrientationDialog(self.arrow_size, self.geditor)
        self.normal_orientation_dialog.orientation_accepted.connect(self.handle_outside_confirmation)
        self.normal_orientation_dialog.size_changed.connect(self.update_arrow_sizes)  # Connect the size change signal
        self.normal_orientation_dialog.show()

    def handle_outside_confirmation(self, confirmed, size):
        self.arrow_size = size
        if confirmed:
            self.populate_data(self.arrows_outside, self.data)
            self.finalize_surface_selection()
            self.particle_source_dialog.show()
        else:
            self.remove_arrows(self.arrows_outside)
            self.add_arrows(self.arrows_inside)
            self.normal_orientation_dialog = NormalOrientationDialog(self.arrow_size, self.geditor)
            self.normal_orientation_dialog.msg_label.setText("Do you want to set normals inside?")
            self.normal_orientation_dialog.orientation_accepted.connect(self.handle_inside_confirmation)
            self.normal_orientation_dialog.size_changed.connect(self.update_arrow_sizes)  # Connect the size change signal
            self.normal_orientation_dialog.show()

    def handle_inside_confirmation(self, confirmed, size):
        self.arrow_size = size
        if confirmed:
            self.populate_data(self.arrows_inside, self.data)
            self.finalize_surface_selection()
            self.particle_source_dialog.show()
        else:
            self.remove_arrows(self.arrows_inside)

    def finalize_surface_selection(self):
        self.remove_arrows(self.arrows_outside)
        self.remove_arrows(self.arrows_inside)

        if not self.data:
            return

        surface_address = next(iter(self.data))
        self.log_console.printInfo(f"Selected surface <{surface_address}> with {self.num_cells} cells inside:")
        for arrow_address, values in self.data.items():
            cellCentre = values['cell_center']
            normal = values['normal']
            self.log_console.printInfo(f"<{surface_address}> | <{arrow_address}>: [{cellCentre[0]:.2f}, {cellCentre[1]:.2f}, {cellCentre[2]:.2f}] - ({normal[0]:.2f}, {normal[1]:.2f}, {normal[2]:.2f})")
            surface_address = next(iter(self.data))

        self.geditor.deselect()

    def confirm_normal_orientation(self, orientation):
        msg_box = QMessageBox(self.geditor)
        msg_box.setWindowTitle("Normal Orientation")
        msg_box.setText(f"Do you want to set normals {orientation}?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)

        result = msg_box.exec_()

        return result == QMessageBox.Yes

    def calculate_normals(self, poly_data):
        normals_filter = vtkPolyDataNormals()
        normals_filter.SetInputData(poly_data)
        normals_filter.ComputePointNormalsOff()
        normals_filter.ComputeCellNormalsOn()
        normals_filter.Update()

        return normals_filter.GetOutput().GetCellData().GetNormals()

    def calculate_cell_center(self, cell):
        cell_center = [0.0, 0.0, 0.0]
        points = cell.GetPoints()
        num_points = points.GetNumberOfPoints()
        for j in range(num_points):
            point = points.GetPoint(j)
            cell_center[0] += point[0]
            cell_center[1] += point[1]
            cell_center[2] += point[2]
        return [coord / num_points for coord in cell_center]

    def create_arrow_actor(self, position, direction, arrow_size):
        arrow_source = vtkArrowSource()
        arrow_source.SetTipLength(0.2)
        arrow_source.SetShaftRadius(0.02)
        arrow_source.SetTipResolution(100)

        transform = vtkTransform()
        transform.Translate(position)
        transform.Scale(arrow_size, arrow_size, arrow_size)

        direction_list = list(direction)
        norm = vtkMath.Norm(direction_list)
        if norm > 0:
            vtkMath.Normalize(direction_list)
            x_axis = [1, 0, 0]
            angle = vtkMath.AngleBetweenVectors(x_axis, direction_list)

            if direction == [-1.0, 0.0, 0.0] or direction == [1.0, 0.0, 0.0]:
                rotation_axis = [0.0, 1.0, 0.0]
            else:
                rotation_axis = [0.0, 0.0, 0.0]
                vtkMath.Cross(x_axis, direction_list, rotation_axis)
                if vtkMath.Norm(rotation_axis) == 0:
                    rotation_axis = [0.0, 1.0, 0.0]
            transform.RotateWXYZ(
                vtkMath.DegreesFromRadians(angle), *rotation_axis)

        transform_filter = vtkTransformPolyDataFilter()
        transform_filter.SetInputConnection(arrow_source.GetOutputPort())
        transform_filter.SetTransform(transform)
        transform_filter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(transform_filter.GetOutputPort())

        arrow_actor = vtkActor()
        arrow_actor.SetMapper(mapper)
        arrow_actor.GetProperty().SetColor(DEFAULT_ARROW_ACTOR_COLOR)

        return arrow_actor
