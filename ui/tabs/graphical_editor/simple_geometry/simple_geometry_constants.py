DEFAULT_SPHERE_PHI_RESOLUTION = 30
DEFAULT_SPHERE_THETA_RESOLUTION = 30
SIMPLE_GEOMETRY_SPHERE_PHI_RESOLUTION_HINT = (
    "Specifies the number of subdivisions around the circumference of the sphere along the longitudinal (phi) direction. "
    "Higher values result in a smoother sphere surface.")
SIMPLE_GEOMETRY_SPHERE_THETA_RESOLUTION_HINT = (
    "Specifies the number of subdivisions along the latitude (theta) direction of the sphere. "
    "Higher values result in a smoother sphere surface.")

DEFAULT_CYLINDER_RESOLUTION = 30
SIMPLE_GEOMETRY_CYLINDER_RESOLUTION_HINT = (
    "Specifies the number of subdivisions around the circumference of the cylinder. "
    "Higher values result in a smoother cylindrical surface.")

DEFAULT_CONE_RESOLUTION = 50

SIMPLE_GEOMETRY_MESH_RESOLUTION_SPHERE_VALUE = 1
SIMPLE_GEOMETRY_MESH_RESOLUTION_VALUE = 3
SIMPLE_GEOMETRY_MESH_RESOLUTION_HINT = "This is a count of subdivisions of the triangle mesh. This field needed for more accurate operation performing (subtract/union/intersection). WARNING: Be careful with values that are close to max value, it can be performance overhead."

SIMPLE_GEOMETRY_TRANSFORMATION_MOVE = "move"
SIMPLE_GEOMETRY_TRANSFORMATION_ROTATE = "rotate"
SIMPLE_GEOMETRY_TRANSFORMATION_SCALE = "scale"
