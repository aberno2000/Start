import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


class MeshRenderer:
    """
    Class to render 3D mesh data using matplotlib.

    Attributes:
    - mesh (list): A list of triangles representing the mesh, where each triangle
                   includes vertices and associated data.
    - counts (list): A list of count values extracted from mesh, to be normalized.
    - colors (list): A list of color values corresponding to the normalized count values.
    - normalize_func (function): A function to normalize data values for color mapping.
    - color_interpolator (function): A function to map normalized data to color values.

    Methods:
    - normalize_data: Normalizes the count data from mesh.
    - interpolate_color: Generates color values based on normalized data.
    - _setup_plot: Initializes the 3D plot with mesh data.
    - _add_sliders: Adds interactive sliders for adjusting plot limits.
    - update: Updates the plot limits based on slider values.
    - show: Displays the plot.
    """

    def __init__(self, mesh, normalize_func=None, color_interpolator=None):
        """
        Initializes the MeshRenderer with mesh data and optional normalization and color interpolation functions.

        Args:
        - mesh (list): Mesh data, each element represents a triangle.
        - normalize_func (function, optional): Function to normalize mesh data values.
        - color_interpolator (function, optional): Function to determine color based on normalized values.
        """
        self.mesh = mesh
        self.max_particle_count = max(triangle[5] for triangle in mesh)
        self.normalize_func = (
            normalize_func if normalize_func is not None else self.default_normalize
        )
        self.color_interpolator = (
            color_interpolator
            if color_interpolator is not None
            else self.default_interpolate_color
        )
        self.counts = [triangle[5] for triangle in self.mesh]
        self.colors = self.interpolate_color(self.normalize_data(self.counts))

        # Initial plot setup
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.init_limits = {"xlim": [0, 150], "ylim": [0, 150], "zlim": [0, 150]}

        self.fig.canvas.mpl_connect("scroll_event", self.on_scroll)
        self._setup_plot()

    def default_normalize(self, data):
        """
        Default normalization function. Normalizes a list of count data.
        """
        return [d / self.max_particle_count for d in data]

    def default_interpolate_color(self, normalized_data):
        """
        Default color interpolation function. Maps normalized data to color values.
        """
        self.colors = [(0, "blue"), (0.5, "yellow"), (1, "red")]
        self.n_bins = [0, 0.5, 1]  # Points in normalized_data for color changes
        self.custom_cmap = LinearSegmentedColormap.from_list(
            'my_custom_cmap', self.colors
        )
        return [self.custom_cmap(value) for value in normalized_data]

    def normalize_data(self, counts):
        """
        Normalizes the count data using the provided normalization function.
        """
        return self.normalize_func(counts)

    def interpolate_color(self, normalized_counts):
        """
        Generates color values for each count using the provided color interpolation function.
        """
        return self.color_interpolator(normalized_counts)

    def _setup_plot(self):
        """
        Set up the initial 3D plot using the mesh data.
        """
        for triangle, color in zip(self.mesh, self.colors):
            vertices = np.array([triangle[1], triangle[2], triangle[3]])
            self.ax.add_collection3d(Poly3DCollection([vertices], facecolors=color))

        self.ax.set_xlim(self.init_limits["xlim"])
        self.ax.set_ylim(self.init_limits["ylim"])
        self.ax.set_zlim(self.init_limits["zlim"])
        
        sm = plt.cm.ScalarMappable(cmap=self.custom_cmap, norm=plt.Normalize(vmin=0, vmax=self.max_particle_count))
        sm._A = []
        cbar = plt.colorbar(sm, ax=self.ax)
        cbar.set_label('Particle Count')

    def on_scroll(self, event):
        """
        Handles mouse scroll event on the plot for zooming in and out.

        Args:
        - event: The scroll event.
        """
        # Get the current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        zlim = self.ax.get_zlim()

        # Set the zoom sensitivity (larger number for faster zooming)
        zoom_sensitivity = 0.115

        # Adjust the axis limits based on the scroll direction
        if event.button == "up":  # Zoom in
            self.ax.set_xlim([limit * (1 - zoom_sensitivity) for limit in xlim])
            self.ax.set_ylim([limit * (1 - zoom_sensitivity) for limit in ylim])
            self.ax.set_zlim([limit * (1 - zoom_sensitivity) for limit in zlim])
        elif event.button == "down":  # Zoom out
            self.ax.set_xlim([limit * (1 + zoom_sensitivity) for limit in xlim])
            self.ax.set_ylim([limit * (1 + zoom_sensitivity) for limit in ylim])
            self.ax.set_zlim([limit * (1 + zoom_sensitivity) for limit in zlim])

        # Redraw the canvas
        self.fig.canvas.draw_idle()

    def show(self):
        """
        Display the plot with interactive sliders.
        """
        plt.show()
