from vtk import (
    vtkRenderer, vtkRenderWindowInteractor,
    vtkPoints, vtkPolyData, vtkCellArray, vtkTriangle,
    vtkFloatArray, vtkPolyDataMapper, vtkActor, vtkLookupTable
)


class MeshVisualizer:
    def __init__(self, renderer: vtkRenderer, mesh_data):
        self.mesh_data = mesh_data
        self.max_count = max(triangle[5] for triangle in self.mesh_data)
        
        self.setup_ui(renderer)
    
    def setup_ui(self, renderer):
        self.setup_renderer(renderer)
        self.setup_interactor()
        self.setup_lookup_table()
        
    def setup_renderer(self, renderer):
        self.renderer = renderer
    
    def setup_interactor(self):
        self.interactor = vtkRenderWindowInteractor()
        self.interactor.SetRenderWindow(self.renderer.GetRenderWindow())
        
    def setup_lookup_table(self):
        self.lookup_table = vtkLookupTable()
        self.lookup_table.SetNumberOfTableValues(256)
        self.lookup_table.SetRange(0, self.max_count)
        for i in range(256):
            ratio = i / 255.0
            self.lookup_table.SetTableValue(i, ratio, 0, 1 - ratio)
        self.lookup_table.Build()
    
    def render_mesh(self):
        points = vtkPoints()
        cells = vtkCellArray()
        scalars = vtkFloatArray()
        scalars.SetNumberOfComponents(1)

        for meshTriangle in self.mesh_data:
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
        mapper.SetLookupTable(self.lookup_table)

        actor = vtkActor()
        actor.SetMapper(mapper)
        self.renderer.AddActor(actor)
        
        return actor
