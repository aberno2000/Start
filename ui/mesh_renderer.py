import vtk

class MeshRenderer:
    def __init__(self, mesh):
        self.mesh = mesh
        self.lookupTable = vtk.vtkLookupTable()
        self.renderer = vtk.vtkRenderer()
        self.setup_colormap()
        
        
    def setup_colormap(self):
        max_count = max(triangle[4] for triangle in self.mesh)
        self.lookupTable.SetRange(0, max_count)
        self.lookupTable.Build()


    def render_mesh(self):
        for triangle in self.mesh:
            # Create points for each vertex of the triangle
            points = vtk.vtkPoints()
            points.InsertNextPoint(triangle[1])
            points.InsertNextPoint(triangle[2])
            points.InsertNextPoint(triangle[3])
            
            # Create a polygon for the points
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(3) # Triangle
            for i in range(3):
                polygon.GetPointIds().SetId(i, i)
            
            # Create a PolyData
            polyData = vtk.vtkPolyData()
            polyData.SetPoints(points)
            polygons = vtk.vtkCellArray()
            polygons.InsertNextCell(polygon)
            polyData.SetPolys(polygons)

            # Map the count value to a color
            color = [0] * 3
            self.lookupTable.GetColor(triangle[4], color)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polyData)

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(color)
            
            self.renderer.AddActor(actor)
    
    
    def add_scalar_bar(self):
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetLookupTable(self.lookupTable)
        scalarBar.SetTitle("Count")
        self.renderer.AddActor2D(scalarBar)
    
    
    def show(self):
        # Setup render window, render window interactor, and renderer
        renderWindow = vtk.vtkRenderWindow()
        renderWindow.AddRenderer(self.renderer)
        renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        
        self.render_mesh()
        self.add_scalar_bar()
        
        renderWindow.Render()
        renderWindowInteractor.Start()
