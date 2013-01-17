from morphologist.gui.object3d import View, Object3D

class DisplayManagerMixin(object):

    def initialize_display(self):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
        
    def create_view(self, parent=None):
        return View(parent)

    def add_object_in_view(self, backend_object, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
   
    def clear_view(self, backend_view):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def clear_views(self, backend_views):
        for view in backend_views:
            self.clear_view(view)

    def set_bgcolor_view(self, backend_view, rgba_color):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
    
    def set_position(self, backend_view, position):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")

    def create_backend_view(self, parent, view_type):
        raise NotImplementedError("DisplayManagerMixin is an abstract class")
        

class ObjectsManagerMixin(object):

    def load_object3d(self, filename):
        return Object3D(filename)
        
    def reload_object(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
            
    def get_object_center_position(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color_map(self, backend_object, color_map_name):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color(self, backend_object, rgba_color):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def create_backend_fusion_object(self, backend_object1, backend_object2, mode, rate):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")

    def load_backend_object(self, filename):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")
    
    def create_backend_point_object(self, coordinates):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")

    def shallow_copy_backend_object(self, backend_object):
        raise NotImplementedError("ObjectsLoaderMixin is an abstract class")


class LoadObjectError(Exception):
    pass

