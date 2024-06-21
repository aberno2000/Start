from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QDialog, QInputDialog
from vtk import vtkPoints, vtkPolyDataMapper, vtkActor, vtkVertexGlyphFilter, vtkPolyData
from styles import DEFAULT_PARTICLE_ACTOR_COLOR, DEFAULT_PARTICLE_ACTOR_SIZE
from logger import LogConsole
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class ParticleAnimator:
    FPS = 120

    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, log_console: LogConsole, renderer, parent=None) -> None:
        self.parent = parent
        self.particle_actors = {}
        self.animation_timer = QTimer(self.parent)
        self.animation_timer.timeout.connect(self.update_animation)
        self.log_console = log_console
        self.vtkWidget = vtkWidget
        self.renderer = renderer

        self.current_iteration = 0
        self.max_iterations = 0
        self.repeat_count = 0
        self.max_repeats = 1
        
    def create_particle_actor(self, points):
        points_vtk = vtkPoints()
        for point in points:
            points_vtk.InsertNextPoint(point.x, point.y, point.z)

        polydata = vtkPolyData()
        polydata.SetPoints(points_vtk)

        vertex_filter = vtkVertexGlyphFilter()
        vertex_filter.SetInputData(polydata)
        vertex_filter.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(vertex_filter.GetOutputPort())

        actor = vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(DEFAULT_PARTICLE_ACTOR_COLOR)
        actor.GetProperty().SetPointSize(DEFAULT_PARTICLE_ACTOR_SIZE)

        return actor

    def animate_particle_movements(self, particles_movement):
        self.particles_movement = particles_movement
        self.current_iteration = 0
        self.repeat_count = 0
        self.settled_actors = {}

        # Determine the maximum number of iterations
        self.max_iterations = max(len(movements)
                                  for movements in particles_movement.values())

        # Initialize vtkPoints with the correct number of points
        num_particles = len(particles_movement)
        self.particle_points = vtkPoints()
        self.particle_points.SetNumberOfPoints(num_particles)

        # Initialize points to a default position
        for i in range(num_particles):
            self.particle_points.SetPoint(i, [0.0, 0.0, 0.0])

        # Create an actor for the points
        self.particle_polydata = vtkPolyData()
        self.particle_polydata.SetPoints(self.particle_points)

        self.vertex_filter = vtkVertexGlyphFilter()
        self.vertex_filter.SetInputData(self.particle_polydata)
        self.vertex_filter.Update()

        self.particle_mapper = vtkPolyDataMapper()
        self.particle_mapper.SetInputConnection(self.vertex_filter.GetOutputPort())

        self.particle_actor = vtkActor()
        self.particle_actor.SetMapper(self.particle_mapper)
        self.particle_actor.GetProperty().SetColor(DEFAULT_PARTICLE_ACTOR_COLOR)
        self.particle_actor.GetProperty().SetPointSize(DEFAULT_PARTICLE_ACTOR_SIZE)

        self.renderer.AddActor(self.particle_actor)

        # Set the timer to update every 1/FPS second
        self.animation_timer.start(1000 / self.FPS)

    def update_animation(self):
        if self.current_iteration >= self.max_iterations * self.FPS:
            self.repeat_count += 1
            if self.repeat_count >= self.max_repeats:
                self.stop_animation()
                return
            self.current_iteration = 0   # Reset iteration to start over
            self.remove_all_particles()  # Clear all particles and stop the animation

        # Calculate frame within the current time step
        time_step = self.current_iteration // self.FPS
        frame_within_step = self.current_iteration % self.FPS

        # Interpolation factor
        t = 0 if self.FPS == 1 else frame_within_step / (self.FPS - 1)

        # Move or create particle actors
        for i, (particle_id, movements) in enumerate(self.particles_movement.items()):
            if time_step < len(movements) - 1:
                pos1 = movements[time_step]
                pos2 = movements[time_step + 1]

                # Calculate the new interpolated position
                new_position = [
                    pos1.x + t * (pos2.x - pos1.x),
                    pos1.y + t * (pos2.y - pos1.y),
                    pos1.z + t * (pos2.z - pos1.z)
                ]

                # Update the position of the particle in vtkPoints
                self.particle_points.SetPoint(i, new_position)

            else:
                if particle_id not in self.settled_actors:
                    settled_position = [
                        movements[-1].x,
                        movements[-1].y,
                        movements[-1].z
                    ]
                    self.particle_points.SetPoint(i, settled_position)
                    self.settled_actors[particle_id] = True

        self.particle_points.Modified()
        self.particle_polydata.Modified()
        self.vtkWidget.GetRenderWindow().Render()
        self.current_iteration += 1

    def remove_all_particles(self):
        if hasattr(self, 'particle_points') and self.particle_points is not None:
            self.particle_points.Reset()
        if hasattr(self, 'particle_polydata') and self.particle_polydata is not None:
            self.particle_polydata.Modified()
        if hasattr(self, 'vertex_filter') and self.vertex_filter is not None:
            self.vertex_filter.Update()
        if hasattr(self, 'particle_mapper') and self.particle_mapper is not None:
            self.particle_mapper.Update()
        self.vtkWidget.GetRenderWindow().Render()

    def stop_animation(self):
        self.animation_timer.stop()
        self.remove_all_particles()

    def show_animation(self):        
        particles_movement = self.load_particle_movements()
        if not particles_movement:
            self.log_console.printError("There is nothing to show. Particles haven't been spawned or simulation hasn't been started")
            return
        self.animate_particle_movements(particles_movement)

    def edit_fps(self):
        fps_dialog = QInputDialog(self.parent)
        fps_dialog.setInputMode(QInputDialog.IntInput)
        fps_dialog.setLabelText("Please enter FPS value (1-300):")
        fps_dialog.setIntRange(1, 300)
        fps_dialog.setIntStep(1)
        fps_dialog.setIntValue(self.FPS)
        fps_dialog.setWindowTitle("Set FPS")

        if fps_dialog.exec_() == QDialog.Accepted:
            self.FPS = fps_dialog.intValue()

    def load_particle_movements(self, filename="particles_movements.json"):
        """
        Load particle movements from a JSON file.

        :param filename: Path to the JSON file.
        :return: Dictionary with particle ID as keys and list of Point objects as values.
        """
        from json import load, JSONDecodeError
        
        try:
            class PointForTracking:
                def __init__(self, x, y, z):
                    self.x = x
                    self.y = y
                    self.z = z
                def __repr__(self):
                    return f"Point(x={self.x}, y={self.y}, z={self.z})"
            
            with open(filename, 'r') as file:
                data = load(file)

            particles_movement = {}
            for particle_id, movements in data.items():
                particle_id = int(particle_id)
                particles_movement[particle_id] = [PointForTracking(movement['x'], movement['y'], movement['z']) for movement in movements]
            return particles_movement

        except FileNotFoundError:
            self.log_console.printError(f"The file {filename} was not found.")
        except JSONDecodeError:
            self.log_console.printError("Error: The file is not a valid JSON.")
        except Exception as e:
            self.log_console.printError(f"Unexpected error: {e}")