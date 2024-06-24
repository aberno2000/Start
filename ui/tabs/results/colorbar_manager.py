from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkRenderer, vtkScalarBarActor, vtkLookupTable, vtkFloatArray, vtkStringArray, vtkActor


class ColorbarManager:
    def __init__(self, vtkWidget: QVTKRenderWindowInteractor, renderer: vtkRenderer, mesh_data, actor: vtkActor):
        self.scalarBar = vtkScalarBarActor()
        self.mesh_data = mesh_data
        self.actor = actor
        self.renderer = renderer
        self.default_num_labels = 5  # Default labels count
        self.setup_colormap()

        # Setting default style of the scalar bar
        self.setup_default_scalarbar_properties()
        
    def setup_default_scalarbar_properties(self):
        self.scalarBar.SetWidth(0.1)
        self.scalarBar.SetHeight(0.75)
        text_property = self.scalarBar.GetLabelTextProperty()
        text_property.SetFontSize(12)
        text_property.SetFontFamilyAsString("Noto Sans SemiBold")
        text_property.SetBold(True)
        text_property.SetItalic(False)
        text_property.SetColor(0, 0, 0)

        title_text_property = self.scalarBar.GetTitleTextProperty()
        title_text_property.SetFontSize(12)
        title_text_property.SetFontFamilyAsString("Noto Sans SemiBold")
        title_text_property.SetBold(True)
        title_text_property.SetItalic(False)
        title_text_property.SetColor(0, 0, 0)

    def setup_colormap(self):
        self.max_count = max(triangle[5] for triangle in self.mesh_data)
        self.setup_lookup_table()
        self.set_annotations(self.default_num_labels)
        
    def setup_lookup_table(self):
        self.lookup_table = vtkLookupTable()
        self.lookup_table.SetNumberOfTableValues(256)
        self.lookup_table.SetRange(0, self.max_count)
        for i in range(256):
            ratio = i / 255.0
            self.lookup_table.SetTableValue(i, ratio, 0, 1 - ratio)
        self.lookup_table.Build()

    def set_annotations(self, num_labels=5):
        from numpy import round, linspace
        
        valuesArray = vtkFloatArray()
        annotationsArray = vtkStringArray()
        unique_values = sorted(set(triangle[5] for triangle in self.mesh_data))

        # Function to pick N evenly spaced elements including the first and the last
        def pick_n_uniformly(lst, n):
            if n >= len(lst):
                return lst
            indeces = round(linspace(0, len(lst) - 1, n)).astype(int)
            return [lst[index] for index in indeces]

        uniform_values = pick_n_uniformly(unique_values, num_labels)
        for value in uniform_values:
            valuesArray.InsertNextValue(value)
            annotationsArray.InsertNextValue(f"{value}")

        self.lookup_table.SetAnnotations(valuesArray, annotationsArray)
        
    def add_colorbar(self, title='Color Scale', range=None):
        self.scalarBar.SetTitle(title)
        self.scalarBar.SetNumberOfLabels(self.default_num_labels)

        if range:
            self.actor.GetMapper().GetLookupTable().SetRange(range[0], range[1])

        self.scalarBar.SetLookupTable(self.actor.GetMapper().GetLookupTable())
        self.renderer.AddActor2D(self.scalarBar)
        
    def apply_scale(self, width: float, height: float):
        self.scalarBar.SetWidth(width)
        self.scalarBar.SetHeight(height)
        
    def change_font(self, font, color_rgb):
        text_property = self.scalarBar.GetLabelTextProperty()
        text_property.SetFontFamilyAsString(font.family())
        text_property.SetFontSize(font.pointSize())
        text_property.SetBold(font.bold())
        text_property.SetItalic(font.italic())
        text_property.SetColor(color_rgb)

        title_text_property = self.scalarBar.GetTitleTextProperty()
        title_text_property.SetFontFamilyAsString(font.family())
        title_text_property.SetFontSize(font.pointSize())
        title_text_property.SetBold(font.bold())
        title_text_property.SetItalic(font.italic())
        title_text_property.SetColor(color_rgb)

        self.vtkWidget.GetRenderWindow().Render()
        
    def change_divs(self, divs: int):
        self.scalarBar.SetNumberOfLabels(divs)
        self.set_annotations(divs)
        
    def reset_to_default(self):
        self.setup_default_scalarbar_properties()
    