from .simple_geometry_constants import SIMPLE_GEOMETRY_TRANSFORMATION_MOVE, SIMPLE_GEOMETRY_TRANSFORMATION_ROTATE, SIMPLE_GEOMETRY_TRANSFORMATION_SCALE
from vtk import vtkTransform, vtkTransformFilter, vtkActor, vtkCleanPolyData, vtkBooleanOperationPolyDataFilter, vtkPolyDataMapper
from util import convert_unstructured_grid_to_polydata
from logger import InternalLogger


class SimpleGeometryTransformer:
    
    @staticmethod
    def transform_actors(action, actors, *args):
        """
        Applies a transformation to the selected actors.

        Parameters:
        action (str): The type of transformation ("move", "rotate", "scale").
        actors: List of the actors.
        *args: Arguments for the transformation.
            For "move" expect three values (x_offset, y_offset, z_offset).
            For "rotate" expect three values (angle_x, angle_y, angle_z).
            For "scale" expect one value (scale_factor).
        """
        try:
            # Create a vtkTransform object based on the action
            transform = vtkTransform()
            if action == SIMPLE_GEOMETRY_TRANSFORMATION_MOVE and len(args) == 3:
                x_offset, y_offset, z_offset = args
                transform.Translate(x_offset, y_offset, z_offset)
            
            elif action == SIMPLE_GEOMETRY_TRANSFORMATION_ROTATE and len(args) == 3:
                angle_x, angle_y, angle_z = args
                transform.RotateX(angle_x)
                transform.RotateY(angle_y)
                transform.RotateZ(angle_z)
            
            elif action == SIMPLE_GEOMETRY_TRANSFORMATION_SCALE and len(args) == 1:
                scale_factor = args[0]
                transform.Scale(scale_factor, scale_factor, scale_factor)
            
            else:
                raise ValueError(f"Invalid arguments for the specified action '{action}'")

            # Apply the transformation to each selected actor
            for actor in actors:
                if actor and isinstance(actor, vtkActor):
                    mapper = actor.GetMapper()
                    if mapper:
                        input_data = mapper.GetInput()
                        transform_filter = vtkTransformFilter()
                        transform_filter.SetTransform(transform)
                        transform_filter.SetInputData(input_data)
                        transform_filter.Update()
                        mapper.SetInputConnection(transform_filter.GetOutputPort())
                        mapper.Update()

                    actor.Modified()
                    
        except Exception as e:
            print(f"An error occurred while transforming actors: {e}")

    @staticmethod
    def object_operation_executor_helper(obj_from: vtkActor, obj_to: vtkActor, operation: vtkBooleanOperationPolyDataFilter):
        try:
            obj_from_subtract_polydata = convert_unstructured_grid_to_polydata(obj_from)
            obj_to_subtract_polydata = convert_unstructured_grid_to_polydata(obj_to)

            cleaner1 = vtkCleanPolyData()
            cleaner1.SetInputData(obj_from_subtract_polydata)
            cleaner1.Update()
            cleaner2 = vtkCleanPolyData()
            cleaner2.SetInputData(obj_to_subtract_polydata)
            cleaner2.Update()

            # Set the input objects for the operation
            operation.SetInputData(0, cleaner1.GetOutput())
            operation.SetInputData(1, cleaner2.GetOutput())

            # Update the filter to perform the subtraction
            operation.Update()

            # Retrieve the result of the subtraction
            resultPolyData = operation.GetOutput()

            # Check if subtraction was successful
            if resultPolyData is None or resultPolyData.GetNumberOfPoints() == 0:
                raise ValueError("Operation Failed: No result from the operation operation.")

            mapper = vtkPolyDataMapper()
            mapper.SetInputData(resultPolyData)

            actor = vtkActor()
            actor.SetMapper(mapper)
            
            return actor
        
        except Exception as e:
            print(InternalLogger.get_warning_none_result_with_exception_msg(e))
            return None

    @staticmethod
    def subtract(obj_from: vtkActor, obj_to: vtkActor) -> vtkActor:
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToDifference()
        return SimpleGeometryTransformer.object_operation_executor_helper(obj_from, obj_to, booleanOperation)

    @staticmethod
    def combine(obj_from: vtkActor, obj_to: vtkActor) -> vtkActor:
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToUnion()
        return SimpleGeometryTransformer.object_operation_executor_helper(obj_from, obj_to, booleanOperation)

    @staticmethod
    def intersect(obj_from: vtkActor, obj_to: vtkActor) -> vtkActor:
        booleanOperation = vtkBooleanOperationPolyDataFilter()
        booleanOperation.SetOperationToIntersection()
        return SimpleGeometryTransformer.object_operation_executor_helper(obj_from, obj_to, booleanOperation)