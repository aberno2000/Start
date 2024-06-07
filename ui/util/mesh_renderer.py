from vtk import(
    vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor,
    vtkLookupTable, vtkPoints, vtkPolyData, vtkCellArray, vtkTriangle,
    vtkFloatArray, vtkPolyDataMapper, vtkActor, vtkScalarBarActor,
    vtkStringArray
)
from numpy import round, linspace

class MeshRenderer:
    def __init__(self, mesh):
        self.mesh = mesh
        self.renderer = vtkRenderer()
        self.renderWindow = vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        
        self.interactor = vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.renderWindow)
        
        self.scalarBar = vtkScalarBarActor()
        self.default_num_labels = 5 # Default labels count
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
        self.max_count = max(triangle[5] for triangle in self.mesh)
        self.lookupTable = vtkLookupTable()
        self.lookupTable.SetNumberOfTableValues(256)
        self.lookupTable.SetRange(0, self.max_count)
        for i in range(256):
            ratio = i / 255.0
            self.lookupTable.SetTableValue(i, ratio, 0, 1 - ratio)
        self.lookupTable.Build()
        self.set_annotations(self.default_num_labels)
        
        
    def set_annotations(self, num_labels=5):
        valuesArray = vtkFloatArray()
        annotationsArray = vtkStringArray()
        unique_values = sorted(set(triangle[5] for triangle in self.mesh))
        
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
        
        self.lookupTable.SetAnnotations(valuesArray, annotationsArray)


    def render_mesh(self):
        points = vtkPoints()
        cells = vtkCellArray()
        scalars = vtkFloatArray()
        scalars.SetNumberOfComponents(1)
        
        for meshTriangle in self.mesh:
            point_ids = []
            for vertex in meshTriangle[1:4]:
                point_id = points.InsertNextPoint(vertex)
                point_ids.append(point_id)

            # Create a triangle cell
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId(0, point_ids[0])
            triangle.GetPointIds().SetId(1, point_ids[1])
            triangle.GetPointIds().SetId(2, point_ids[2])
            cells.InsertNextCell(triangle)

            # Add the scalar value for the triangle
            scalars.InsertNextValue(meshTriangle[5])

        polyData = vtkPolyData()
        polyData.SetPoints(points)
        polyData.SetPolys(cells)
        polyData.GetCellData().SetScalars(scalars)

        mapper = vtkPolyDataMapper()
        mapper.SetInputData(polyData)
        mapper.SetScalarRange(0, self.max_count)
        mapper.SetLookupTable(self.lookupTable)

        self.actor = vtkActor()
        self.actor.SetMapper(mapper)
        self.renderer.AddActor(self.actor)

        
    def add_colorbar(self, title='Color Scale', range=None): 
        self.scalarBar.SetTitle(title)
        self.scalarBar.SetNumberOfLabels(self.default_num_labels)

        if range:
            self.actor.GetMapper().GetLookupTable().SetRange(range[0], range[1])

        self.scalarBar.SetLookupTable(self.actor.GetMapper().GetLookupTable())
        self.renderer.AddActor2D(self.scalarBar)


    def show(self):
        self.render_mesh()
        self.add_scalar_bar()
        self.renderWindow.Render()
        self.interactor.Start()
        
