from morphologist.gui.object3d import View, Object3D

class DisplayManagerMixin(object):

    def initialize_display(self):
        raise Exception("DisplayManagerMixin is an abstract class")
        
    def create_view(self, parent=None):
        return View(parent)

    def add_object_in_view(self, object, view):
        raise Exception("DisplayManagerMixin is an abstract class")
   
    def clear_view(self, view):
        raise Exception("DisplayManagerMixin is an abstract class")
    
    def clear_views(self, views):
        for view in views:
            self.clear_view(view)

    def set_bgcolor_view(self, view, rgba_color):
        raise Exception("DisplayManagerMixin is an abstract class")
    
    def set_position(self, view, position):
        raise Exception("DisplayManagerMixin is an abstract class")

    def _friend_create_backend_view(self, parent=None):
        raise Exception("DisplayManagerMixin is an abstract class")
        

class ObjectsManagerMixin(object):

    def load_object3d(self, filename):
        return Object3D(filename)
        
    def reload_object(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")
            
    def get_object_center_position(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color_map(self, object, color_map_name):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color(self, object, rgba_color):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def _friend_create_backend_fusion_object(self, object1, object2, mode, rate):
        raise Exception("ObjectsLoaderMixin is an abstract class")

    def _friend_load_backend_object(self, filename):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def _friend_create_backend_point_object(self, coordinates):
        raise Exception("ObjectsLoaderMixin is an abstract class")

    def _friend_shallow_copy_backend_object(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")


class LoadObjectError(Exception):
    pass

