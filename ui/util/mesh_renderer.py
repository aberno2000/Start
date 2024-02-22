import vtk

class MeshRenderer:
    def __init__(self, mesh):
        self.mesh = mesh
        self.renderer = vtk.vtkRenderer()
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.renderWindow)
        self.setup_colormap()


    def setup_colormap(self):
        self.max_count = max(triangle[5] for triangle in self.mesh)
        self.lookupTable = vtk.vtkLookupTable()
        self.lookupTable.SetNumberOfTableValues(256)
        self.lookupTable.SetRange(0, self.max_count)
        for i in range(256):
            ratio = i / 255.0
            self.lookupTable.SetTableValue(i, ratio, 0, 1 - ratio)
        self.lookupTable.Build()


    def render_mesh(self):
        for meshTriangle in self.mesh:
            points = vtk.vtkPoints()
            polyData = vtk.vtkPolyData()
            cells = vtk.vtkCellArray()

            for vertex in meshTriangle[1:4]:
                points.InsertNextPoint(vertex)
            
            # Create a polygon for the points
            triangle = vtk.vtkTriangle()
            triangle.GetPointIds().SetId(0, 0)
            triangle.GetPointIds().SetId(1, 1)
            triangle.GetPointIds().SetId(2, 2)
            cells.InsertNextCell(triangle)
            
            polyData.SetPoints(points)
            polyData.SetPolys(cells)

            # Map the count value (scalar) to a color
            scalars = vtk.vtkFloatArray()
            scalars.SetNumberOfComponents(1)
            scalars.InsertNextValue(meshTriangle[5])

            polyData.GetCellData().SetScalars(scalars)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polyData)
            mapper.SetScalarRange(0, self.max_count)
            mapper.SetLookupTable(self.lookupTable)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            self.renderer.AddActor(actor)



    def add_scalar_bar(self):
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetLookupTable(self.lookupTable)
        scalarBar.SetTitle("Particle Count")
        scalarBar.SetNumberOfLabels(4)
        self.renderer.AddActor2D(scalarBar)


    def show(self):
        self.render_mesh()
        self.add_scalar_bar()
        self.renderWindow.Render()
        self.interactor.Start()
