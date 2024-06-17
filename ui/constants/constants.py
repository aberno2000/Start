from re import compile

DEFAULT_TEMP_MESH_FILE = 'temp.msh'
DEFAULT_TEMP_VTK_FILE = 'temp.vtk'
DEFAULT_TEMP_HDF5_FILE = 'temp.hdf5'
DEFAULT_TEMP_CONFIG_FILE = 'temp_config.json'

DEFAULT_COUNT_OF_PROJECT_FILES = 3

ANSI_COLOR_REGEX = compile(r'\033\[(\d+)(;\d+)*m')
ANSI_TO_QCOLOR = {
    '31': 'red',
    '33': 'yellow',
    '32': 'green',
    '35': 'purple',
    '37': 'white',
    '0': 'light gray'
}

INTERACTOR_STYLE_TRACKBALL_CAMERA = 'trackball_camera'
INTERACTOR_STYLE_TRACKBALL_ACTOR = 'trackball_actor'
INTERACTOR_STYLE_RUBBER_AND_PICK = 'rubber_and_pick'

ACTION_ACTOR_CREATING = 'create_actor'
ACTION_ACTOR_TRANSFORMATION = 'transform_actor'

DEFAULT_LINE_EDIT_WIDTH = 175
DEFAULT_COMBOBOX_WIDTH = 85
