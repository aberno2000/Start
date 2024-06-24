import json
from math import pi
from PyQt5.QtWidgets import QMessageBox, QDialog
from vtk import vtkTransform, vtkActor
from vtkmodules.vtkFiltersSources import vtkArrowSource
from vtkmodules.vtkFiltersGeneral import vtkTransformPolyDataFilter
from vtkmodules.vtkRenderingCore import vtkPolyDataMapper
from util import rad_to_degree, extract_transform_from_actor, calculate_thetaPhi, calculate_thetaPhi_with_angles
from dialogs import *
from styles import DEFAULT_ARROW_SCALE, DEFAULT_ARROW_ACTOR_COLOR


class ParticleSourceManager:
    def __init__(self, vtk_widget, renderer, log_console, config_tab, selected_actors, statusBar, parent=None):
        self.vtkWidget = vtk_widget
        self.renderer = renderer
        self.log_console = log_console
        self.config_tab = config_tab
        self.selected_actors = selected_actors
        self.particleSourceArrowActor = None
        self.expansion_angle = None
        self.parent = parent
        self.statusBar = statusBar

    def save_point_particle_source_to_config(self):
        try:
            base_coords = self.get_particle_source_base_coords()
            if base_coords is None:
                raise ValueError("Base coordinates are not defined")

            if not self.expansion_angle:
                self.log_console.printError("Expansion angle θ is undefined")
                raise ValueError("Expansion angle θ is undefined")

            if self.get_particle_source_direction() is None:
                return
            theta, phi = self.get_particle_source_direction()

            config_file = self.config_tab.config_file_path
            if not config_file:
                QMessageBox.warning(self.parent, "Saving Particle Source as Point",
                                    "Can't save pointed particle source, first you need to choose a configuration file, then set the source")
                self.reset_particle_source_arrow()
                return

            # Read the existing configuration file
            with open(config_file, 'r') as file:
                config_data = json.load(file)

            # Check for existing sources and ask user if they want to remove them
            sources_to_remove = []
            if "ParticleSourcePoint" in config_data:
                sources_to_remove.append("ParticleSourcePoint")
            if "ParticleSourceSurface" in config_data:
                sources_to_remove.append("ParticleSourceSurface")

            if sources_to_remove:
                reply = QMessageBox.question(self.parent, "Remove Existing Sources",
                                             f"The configuration file contains existing sources: {', '.join(sources_to_remove)}. Do you want to remove them?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    for source in sources_to_remove:
                        del config_data[source]

            self.particle_source_dialog = ParticleSourceDialog(self.parent)
            self.particle_source_dialog.accepted_signal.connect(lambda params: self.handle_particle_source_point_accepted(
                params, config_file, config_data, theta, phi, base_coords))
            self.particle_source_dialog.rejected_signal.connect(
                self.reset_particle_source_arrow)
            self.particle_source_dialog.show()

        except Exception as e:
            self.log_console.printError(f"Error defining particle source. {e}")
            QMessageBox.warning(self.parent, "Particle Source",
                                f"Error defining particle source. {e}")
            return None

    def save_point_particle_source_to_config_with_theta_phi(self, x, y, z, theta, phi):
        try:
            if not self.expansion_angle:
                self.log_console.printError("Expansion angle θ is undefined")
                raise ValueError("Expansion angle θ is undefined")

            config_file = self.config_tab.config_file_path
            if not config_file:
                QMessageBox.warning(self.parent, "Saving Particle Source as Point",
                                    "Can't save pointed particle source, first you need to choose a configuration file, then set the source")
                self.reset_particle_source_arrow()
                return

            # Read the existing configuration file
            with open(config_file, 'r') as file:
                config_data = json.load(file)

            # Check for existing sources and ask user if they want to remove them
            sources_to_remove = []
            if "ParticleSourcePoint" in config_data:
                sources_to_remove.append("ParticleSourcePoint")
            if "ParticleSourceSurface" in config_data:
                sources_to_remove.append("ParticleSourceSurface")

            if sources_to_remove:
                reply = QMessageBox.question(self.parent, "Remove Existing Sources",
                                             f"The configuration file contains existing sources: {', '.join(sources_to_remove)}. Do you want to remove them?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    for source in sources_to_remove:
                        del config_data[source]

            self.particle_source_dialog = ParticleSourceDialog(self.parent)
            self.particle_source_dialog.accepted_signal.connect(lambda params: self.handle_particle_source_point_accepted(
                params, config_file, config_data, theta, phi, [x, y, z]))
            self.particle_source_dialog.rejected_signal.connect(
                self.reset_particle_source_arrow)
            self.particle_source_dialog.show()

        except Exception as e:
            self.log_console.printError(f"Error defining particle source. {e}")
            QMessageBox.warning(self.parent, "Particle Source",
                                f"Error defining particle source. {e}")
            return None

    def handle_particle_source_point_accepted(self, particle_params, config_file, config_data, theta, phi, base_coords):
        try:
            particle_type = particle_params["particle_type"]
            energy = particle_params["energy"]
            num_particles = particle_params["num_particles"]

            # Prepare new ParticleSourcePoint entry
            if "ParticleSourcePoint" not in config_data:
                config_data["ParticleSourcePoint"] = {}

            new_point_index = str(len(config_data["ParticleSourcePoint"]) + 1)
            config_data["ParticleSourcePoint"][new_point_index] = {
                "Type": particle_type,
                "Count": num_particles,
                "Energy": energy,
                "phi": phi,
                "theta": theta,
                "expansionAngle": self.expansion_angle,
                "BaseCoordinates": [base_coords[0], base_coords[1], base_coords[2]]
            }

            # Write the updated configuration back to the file
            with open(config_file, 'w') as file:
                json.dump(config_data, file, indent=4)

            self.statusBar.showMessage("Successfully set particle source as point source and calculated direction angles")
            self.log_console.printInfo(f"Successfully written coordinates of the particle source:\n"
                                       f"Base: {base_coords}\n"
                                       f"Expansion angle θ: {self.expansion_angle} ({rad_to_degree(self.expansion_angle)}°)\n"
                                       f"Polar (colatitude) angle θ: {theta} ({rad_to_degree(theta)}°)\n"
                                       f"Azimuthal angle φ: {phi} ({rad_to_degree(phi)}°)\n"
                                       f"Particle Type: {particle_type}\n"
                                       f"Energy: {energy} eV\n"
                                       f"Number of Particles: {num_particles}")

            self.reset_particle_source_arrow()
        except Exception as e:
            self.log_console.printError(f"Error saving particle source. {e}")
            QMessageBox.warning(self.parent, "Particle Source",
                                f"Error saving particle source. {e}")
            return None

    def reset_particle_source_arrow(self):
        self.parent.remove_actor(self.particleSourceArrowActor)
        self.particleSourceArrowActor = None

    def get_particle_source_base_coords(self):
        if not self.particleSourceArrowActor or not isinstance(self.particleSourceArrowActor, vtkActor):
            return None
        return self.particleSourceArrowActor.GetPosition()

    def get_particle_source_arrow_tip_coords(self):
        if not self.particleSourceArrowActor:
            return

        transform = extract_transform_from_actor(self.particleSourceArrowActor)
        init_tip_coords = [0, 0, 1]
        global_tip_coords = transform.TransformPoint(init_tip_coords)

        return global_tip_coords

    def get_particle_source_direction(self):
        if not self.particleSourceArrowActor:
            return

        base_coords = self.get_particle_source_base_coords()
        tip_coords = self.get_particle_source_arrow_tip_coords()

        try:
            theta, phi = calculate_thetaPhi(base_coords, tip_coords)
        except Exception as e:
            self.log_console.printError(f"An error occured when calculating polar (colatitude) θ and azimuthal φ: {e}\n")
            QMessageBox.warning(self.parent, "Invalid Angles", f"An error occured when calculating polar (colatitude) θ and azimuthal φ: {e}")
            return None

        return theta, phi

    def create_direction_arrow_interactively(self):
        arrowSource = vtkArrowSource()
        arrowSource.SetTipLength(0.25)
        arrowSource.SetTipRadius(0.1)
        arrowSource.SetShaftRadius(0.01)
        arrowSource.Update()
        arrowSource.SetTipResolution(100)

        arrowTransform = vtkTransform()
        arrowTransform.RotateX(90)
        arrowTransform.RotateWXYZ(90, 0, 0, 1)  # Initial direction by Z-axis.
        arrowTransform.Scale(DEFAULT_ARROW_SCALE)
        arrowTransformFilter = vtkTransformPolyDataFilter()
        arrowTransformFilter.SetTransform(arrowTransform)
        arrowTransformFilter.SetInputConnection(arrowSource.GetOutputPort())
        arrowTransformFilter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(arrowTransformFilter.GetOutputPort())

        self.particleSourceArrowActor = vtkActor()
        self.particleSourceArrowActor.SetMapper(mapper)
        self.particleSourceArrowActor.GetProperty().SetColor(DEFAULT_ARROW_ACTOR_COLOR)
        self.parent.add_actor(self.particleSourceArrowActor)

    def set_particle_source(self):
        if not self.config_tab.mesh_file:
            QMessageBox.warning(self.parent, "Setting Particle Source",
                                "First you need to upload mesh/config, then you can set particle source")
            return

        dialog = ParticleSourceTypeDialog(self.parent)
        if dialog.exec_() == QDialog.Accepted:
            selected_source_type = dialog.getSelectedSourceType()

            if selected_source_type == "Point Source with Conical Distribution":
                self.set_particle_source_as_point()
            elif selected_source_type == "Surface Source":
                self.set_particle_source_as_surface()

    def set_particle_source_as_point(self):
        if not self.particleSourceArrowActor:
            method_dialog = ArrowMethodSelectionDialog(self.parent)
            if method_dialog.exec_() == QDialog.Accepted:
                method = method_dialog.get_selected_method()
                if method == "manual":
                    dialog = ArrowPropertiesDialog(self.vtkWidget, self.renderer, self.particleSourceArrowActor, self.parent)
                    dialog.properties_accepted.connect(self.on_arrow_properties_accepted)
                    dialog.show()
                elif method == "interactive":
                    self.create_direction_arrow_interactively()

                    self.expansion_angle_dialog = ExpansionAngleDialogNonModal(self.vtkWidget, self.renderer, self.parent)
                    self.expansion_angle_dialog.accepted_signal.connect(self.handle_theta_signal)
                    self.expansion_angle_dialog.show()
                else:
                    QMessageBox.information(self.parent, "Pointed Particle Source",
                                            f"Can't apply method {method} to the pointed particle source")
                    self.reset_particle_source_arrow()
                    return

    def on_arrow_properties_accepted(self, properties):
        x, y, z, angle_x, angle_y, angle_z, arrow_size = properties
        theta, phi = calculate_thetaPhi_with_angles(
            x, y, z, angle_x, angle_y, angle_z)
        self.expansion_angle_dialog = ExpansionAngleDialogNonModal(self.vtkWidget, self.renderer, self.parent)
        self.expansion_angle_dialog.accepted_signal.connect(
            lambda thetaMax: self.handle_theta_signal_with_thetaPhi(x, y, z, thetaMax, theta, phi))
        self.expansion_angle_dialog.show()

    def handle_theta_signal(self, thetaMax):
        try:
            self.expansion_angle = thetaMax

            if self.get_particle_source_direction() is None:
                self.reset_particle_source_arrow()
                return
            _, phi = self.get_particle_source_direction()

            if thetaMax > pi / 2.:
                self.log_console.printWarning(f"The θ angle exceeds 90°, so some particles can distribute in the opposite direction\nθ = {thetaMax} ({thetaMax * 180. / pi}°)")
            self.log_console.printInfo(f"Successfully assigned values to the expansion angle and calculated φ angle\nθ = {thetaMax} ({thetaMax * 180. / pi}°)\nφ = {phi} ({phi * 180. / pi}°)\n")

            self.save_point_particle_source_to_config()
            self.log_console.printInfo("Particle source set")

        except Exception as e:
            self.reset_particle_source_arrow()
            QMessageBox.critical(self.parent, "Scattering angles", f"Exception while assigning expansion angle θ: {e}")
            self.log_console.printError(f"Exception while assigning expansion angle θ: {e}\n")
            return

    def handle_theta_signal_with_thetaPhi(self, x, y, z, thetaMax, theta, phi):
        try:
            self.expansion_angle = thetaMax

            if thetaMax > pi / 2.:
                self.log_console.printWarning(f"The θ angle exceeds 90°, so some particles can distribute in the opposite direction\nθ = {thetaMax} ({thetaMax * 180. / pi}°)")
            self.log_console.printInfo(f"Successfully assigned values to the expansion angle and calculated φ angle\nθ = {thetaMax} ({thetaMax * 180. / pi}°)\nφ = {phi} ({phi * 180. / pi}°)\n")

            self.save_point_particle_source_to_config_with_theta_phi(x, y, z, theta, phi)
            self.log_console.printInfo("Particle source set")

        except Exception as e:
            self.reset_particle_source_arrow()
            QMessageBox.critical(self.parent, "Scattering angles", f"Exception while assigning expansion angle θ: {e}")
            self.log_console.printError(f"Exception while assigning expansion angle θ: {e}\n")
            return

    def set_particle_source_as_surface(self):
        manager = SurfaceAndArrowManager(self.vtkWidget, self.renderer, self.log_console, self.selected_actors, self)
        manager.set_particle_source_as_surface()
