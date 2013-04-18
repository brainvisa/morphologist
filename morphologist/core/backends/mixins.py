class DisplayManagerMixin(object):

    def add_object_in_view(self, backend_object, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
   
    def clear_view(self, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
        
    def reset_view_camera(self, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def set_bgcolor_view(self, backend_view, rgba_color):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def set_position(self, backend_view, position):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")

    def create_view(self, parent, view_type, restricted_controls=True):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def get_view_type(self, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def set_view_type(self, backend_view, view_type):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    
class ObjectsManagerMixin(object):
        
    def reload_object(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
            
    def get_object_center_position(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color_map(self, backend_object, color_map_name):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color(self, backend_object, rgba_color):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def create_fusion_object(self, backend_object1, backend_object2, mode, rate):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")

    def load_object(self, filename):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def create_point_object(self, coordinates):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")

    def shallow_copy_object(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")


class VectorGraphicsManagerMixin(object):

    def create_view(self, parent):
        raise NotImplementedError("VectorGraphicsManagerMixin is an abstract class")

    def clear_view(self, backend_view):
        raise NotImplementedError("VectorGraphicsManagerMixin is an abstract class")

    def add_object_in_view(self, backend_object, backend_view):
        raise NotImplementedError("VectorGraphicsManagerMixin is an abstract class")

    def set_bgcolor_view(self, backend_view, color):
        raise NotImplementedError("VectorGraphicsManagerMixin is an abstract class")

    def load_histogram(self, filename):
        raise NotImplementedError("VectorGraphicsManagerMixin is an abstract class")


class LoadObjectError(Exception):
    pass


class ColorMap:
    RAINBOW_MASK = "rainbow_mask"
    GREEN_MASK = "green_mask"
    RAINBOW = "rainbow"


class ViewType:
    AXIAL = "Axial"
    SAGITTAL = "Sagittal"
    CORONAL = "Coronal"
    THREE_D = "3D"
    
