from morphologist.core.backends import Backend
from morphologist.core.utils.design_patterns import Visitable


class AbstractObject3D(Visitable):
    
    def __init__(self):
        self._backend = Backend.objects_loader_backend()
        self._friend_backend_object = None
        
    def reload(self):
        raise NotImplementedError("AbstractObject3D is an abstract class")
            
    def get_center_position(self):
        raise NotImplementedError("AbstractObject3D is an abstract class")

    def set_color_map(self, color_map_name):
        self._backend.set_object_color_map(self._friend_backend_object, color_map_name)
    
    def set_color(self, rgba_color):
        self._backend.set_object_color(self._friend_backend_object, rgba_color)

    def _friend_accept_visitor(self, visitor):
        visitor._friend_visit(self)
        
    
class Object3D(AbstractObject3D):
    
    def __init__(self, _enable_init=False):
        super(Object3D, self).__init__()
        if not _enable_init:
            raise Exception("Default constructor not allowed, use from_* static methods instead.")
     
    @classmethod
    def from_filename(cls, filename):
        object3d = cls(_enable_init=True)
        object3d._friend_backend_object = object3d._backend.load_object(filename)
        return object3d
    
    @classmethod    
    def from_fusion(cls, object1, object2, mode, rate):
        object3d = cls(_enable_init=True)
        object3d._friend_backend_object = object3d._backend.create_fusion_object(\
                                                         object1._friend_backend_object, 
                                                         object2._friend_backend_object, 
                                                         mode, rate)
        return object3d
        
    def reload(self):
        self._backend.reload_object(self._friend_backend_object)
    
    def shallow_copy(self):
        object_copy = Object3D(_enable_init=True)
        object_copy._friend_backend_object = self._backend.shallow_copy_object(self._friend_backend_object)
        return object_copy
        
    def get_center_position(self):
        return self._backend.get_object_center_position(self._friend_backend_object)


class PointObject(AbstractObject3D):
    
    def __init__(self, coordinates):
        super(PointObject, self).__init__()
        self._coordinates = coordinates
        self._friend_backend_object = self._backend.create_point_object(coordinates)
    
    def reload(self):
        self._friend_backend_object = self._backend.create_point_object(self._coordinates)
        
    def get_center_position(self):
        return self._coordinates
   

class GroupObject(AbstractObject3D):
    
    def __init__(self, objects):
        super(GroupObject, self).__init__()
        self._objects = objects

    def reload(self):
        for object in self._objects:
            object.reload()
            
    def get_center_position(self):
        if len(self._objects) > 0:
            position = self._objects[0].get_center_position()
        else:
            position = (0,0,0)
        return position

    def set_color_map(self, color_map_name):
        for object in self._objects:
            object.set_color_map(color_map_name)
    
    def set_color(self, rgba_color):
        for object in self._objects:
            object.set_color(rgba_color)
           
    def _friend_accept_visitor(self, visitor):
        for object in self._objects:
            visitor._friend_visit(object)

           
class APCObject(GroupObject):
    
    def __init__(self, filename):
        super(APCObject, self).__init__([])
        self._filename = filename
        self._init_apc_object()
        
    def _init_apc_object(self):
        self._init_coordinates()
        self._ac_object = PointObject(self._ac_coordinates)
        self._pc_object = PointObject(self._pc_coordinates)
        self._ih_object = PointObject(self._ih_coordinates)
        self._objects = [self._ac_object, self._pc_object, self._ih_object]
        
    def _init_coordinates(self):
        apcfile = open(self._filename, "r")
        lines = apcfile.readlines()
        for l in lines:
            if l[:5] == 'ACmm:':
                self._ac_coordinates = map( lambda x: float(x), l.split()[1:4] )
            elif l[:5] == 'PCmm:':
                self._pc_coordinates = map( lambda x: float(x), l.split()[1:4] )
            elif l[:5] == 'IHmm:':
                self._ih_coordinates = map( lambda x: float(x), l.split()[1:4] )

    def reload(self):
        self._init_apc_object()
        
    def get_center_position(self):
        return self._ac_coordinates
    
    def set_ac_color(self, rgba_color):
        self._ac_object.set_color(rgba_color)

    def set_pc_color(self, rgba_color):
        self._pc_object.set_color(rgba_color)

    def set_ih_color(self, rgba_color):
        self._ih_object.set_color(rgba_color)
    
    
class View(object):
    
    def __init__(self, parent, view_type):
        self._backend = Backend.display_backend()
        self._backend_view = self._backend.create_view(parent, view_type)
        
    @property
    def view_type(self):
        return self._backend.get_view_type(self._backend_view)
        
    def add_object(self, object):
        object._friend_accept_visitor(self)
                
    def clear(self):
        self._backend.clear_view(self._backend_view)
    
    def reset_camera(self):
        self._backend.reset_view_camera(self._backend_view)
        
    def center_on_object(self, object):
        position = object.get_center_position()
        self.set_position(position)
    
    def set_position(self, coordinates):
        self._backend.set_position(self._backend_view, coordinates)
    
    def set_bgcolor(self, color):
        self._backend.set_bgcolor_view(self._backend_view, color)
        
    def _friend_visit(self, object3d):
        self._backend.add_object_in_view(object3d._friend_backend_object, self._backend_view)
