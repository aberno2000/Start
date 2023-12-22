import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

if len(sys.argv) != 2:
    print("Usage: python Visualize.py filename")
    sys.exit(1)

file_path = sys.argv[1]
try:
    with open(file_path, "r") as file:
        lines = file.readlines()
except FileNotFoundError:
    print("File not found.")
    sys.exit(1)

particles = []
for line in lines:
    values = line.strip().split()
    particles.append([float(value) for value in values])

# Unpack particle coordinates, velocities and radii
x, y, z, vx, vy, vz, radius = zip(*particles)

# Create a figure and a 3D axis
fig = plt.figure()
ax = fig.add_subplot(111, projection="3d")
bounds = [0, 100]


def draw_line(p1, p2):
    ax.plot3D([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], color="black")


# Define the eight vertices of the cube
vertices = [
    [bounds[0], bounds[0], bounds[0]],
    [bounds[0], bounds[0], bounds[1]],
    [bounds[0], bounds[1], bounds[0]],
    [bounds[0], bounds[1], bounds[1]],
    [bounds[1], bounds[0], bounds[0]],
    [bounds[1], bounds[0], bounds[1]],
    [bounds[1], bounds[1], bounds[0]],
    [bounds[1], bounds[1], bounds[1]],
]

# Define the edges of the cube using the vertices
edges = [
    [vertices[0], vertices[1]],
    [vertices[0], vertices[2]],
    [vertices[0], vertices[4]],
    [vertices[1], vertices[3]],
    [vertices[1], vertices[5]],
    [vertices[2], vertices[3]],
    [vertices[2], vertices[6]],
    [vertices[3], vertices[7]],
    [vertices[4], vertices[5]],
    [vertices[4], vertices[6]],
    [vertices[5], vertices[7]],
    [vertices[6], vertices[7]],
]

# Plot the edges of the cube
for edge in edges:
    draw_line(edge[0], edge[1])

# Scatter plot of particles
colors = ["blue" if r < 0.7 else "red" for r in radius]
scatter = ax.scatter(x, y, z, s=[r for r in radius], c=colors)

# Defining simulation initial time and time step
time = 0
time_step = 0.1
total_frames = 100


# Define the update function for animation
def update(frame):
    # Update particle positions based on velocities
    for i in range(len(x)):
        x[i] += vx[i] * time_step
        y[i] += vy[i] * time_step
        z[i] += vz[i] * time_step

    # Update scatter plot data
    scatter._offsets3d = (x, y, z)
    return (scatter,)


# Create the animation
ani = FuncAnimation(fig, update, frames=total_frames, interval=100, blit=True)
plt.colorbar(scatter, ax=ax, label="Radii")  # Add colorbar


# Event handler for mouse scroll (zooming)
def on_scroll(event):
    axtemp = event.inaxes
    factor = 1.1 if event.step > 0 else 0.9  # Zoom factor
    xlim = axtemp.get_xlim()
    ylim = axtemp.get_ylim()
    zlim = axtemp.get_zlim()
    x_center = sum(xlim) / 2
    y_center = sum(ylim) / 2
    z_center = sum(zlim) / 2
    axtemp.set_xlim(
        [
            x_center - (x_center - xlim[0]) * factor,
            x_center + (xlim[1] - x_center) * factor,
        ]
    )
    axtemp.set_ylim(
        [
            y_center - (y_center - ylim[0]) * factor,
            y_center + (ylim[1] - y_center) * factor,
        ]
    )
    axtemp.set_zlim(
        [
            z_center - (z_center - zlim[0]) * factor,
            z_center + (zlim[1] - z_center) * factor,
        ]
    )
    plt.draw()


# Attach the event handler for mouse scroll
fig.canvas.mpl_connect("scroll_event", on_scroll)

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("Particles in a Bounded Volume")
plt.show()
