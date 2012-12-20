from morphologist import settings


class Backend(object):
    DISPLAY_ROLE = 'display_backend'
    OBJECTS_LOADER_ROLE = 'objects_backend'
    _backend_instance = {}
    _backend_loading_info = {
        'pyanatomist' : ('morphologist.backends.pyanatomist_backend',
                         'PyanatomistBackend')
    }

    @classmethod
    def display_backend(cls):
        return cls.backend_from_role(cls.DISPLAY_ROLE)

    @classmethod
    def select_display_backend(cls, backend_name):
        cls.select_backend_from_role(cls.DISPLAY_ROLE)

    @classmethod
    def objects_loader_backend(cls):
        return cls.backend_from_role(cls.OBJECTS_LOADER_ROLE)

    @classmethod
    def select_objects_loader_backend(cls, backend_name):
        cls.select_backend_from_role(cls.OBJECTS_LOADER_ROLE)

    @classmethod
    def backend_from_role(cls, role):
        try:
            instance = cls._backend_instance[role]
        except KeyError:
            cls.select_backend_from_role(role, settings[cls.DISPLAY_ROLE])
            instance = cls._backend_instance[role]
        return instance

    @classmethod
    def select_backend_from_role(cls, role, backend_name):
        Cls = cls._get_backend_class(backend_name)
        cls._backend_instance[role] = Cls()

    @classmethod
    def _get_backend_class(cls, backend_name):
        modulename, classname = cls._backend_loading_info[backend_name]
        try:
            module = __import__(modulename, fromlist=classname)
            BackendClass = module.__getattribute__(classname)
        except ImportError, e:
            raise ValueError("invalid backend : '%s' (%s)" % (backend_name, e))
        return BackendClass


class DisplayManagerMixin(object):

    def initialize_display(self):
        raise Exception("DisplayManagerMixin is an abstract class")

    # this method should be used only by the View object ("friend" method)
    def create_backend_view(self, parent=None):
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


class View(object):
      
    def __init__(self, parent=None):
        self._backend = Backend.display_backend()
        # this object should be used only by the backend. It is a "friend" member
        self.backend_view = self._backend.create_backend_view(parent)
        
    def add_object(self, object):
        object.add_in_view(self)
        
    def add_object3d(self, object3d):
        self._backend.add_object_in_view(object3d, self)
        
    def clear(self):
        self._backend.clear_view(self)
    
    def center_on_object(self, object):
        position = object.get_center_position()
        self.set_position(position)
    
    def set_position(self, coordinates):
        self._backend.set_position(self, coordinates)
    
    def set_bgcolor(self, color):
        self._backend.set_bgcolor_view(self, color)
        

class ObjectsManagerMixin(object):

    def load_object3d(self, filename):
        return Object3D(filename)
    
    def load_backend_object(self, filename):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def create_backend_point_object(self, coordinates):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def reload_object(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def get_object_center_position(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color_map(self, object, color_map_name):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    def set_object_color(self, object, rgba_color):
        raise Exception("ObjectsLoaderMixin is an abstract class")
    
    
class LoadObjectError(Exception):
    pass


class AbstractObject3D(object):
    
    def __init__(self):
        self._backend = Backend.objects_loader_backend()
        
    def reload(self):
        raise Exception("AbstractObject3D is an abstract class")
    
    def add_in_view(self, view):
        view.add_object3d(self)
        
    def get_center_position(self):
        raise Exception("AbstractObject3D is an abstract class")

    def set_color_map(self, color_map_name):
        self._backend.set_object_color_map(self, color_map_name)
    
    def set_color(self, rgba_color):
        self._backend.set_object_color(self, rgba_color)
        
    
class Object3D(AbstractObject3D):
    
    def __init__(self, filename):
        super(Object3D, self).__init__()
        self._filename = filename
        self.backend_object = self._backend.load_backend_object(filename)
     
    def reload(self):
        self._backend.reload_object(self)
    
    def get_center_position(self):
        self._backend.get_object_center_position(self)
        

class PointObject(AbstractObject3D):
    
    def __init__(self, coordinates):
        super(PointObject, self).__init__()
        self._coordinates = coordinates
        self.backend_object = self._backend.create_backend_point_object(coordinates)
    
    def reload(self):
        self.backend_object = self._backend.create_backend_point_object(self._coordinates)
        
    def get_center_position(self):
        return self._coordinates
   
    
class GroupObject(AbstractObject3D):
    
    def __init__(self, objects):
        super(GroupObject, self).__init__()
        self._objects = objects

    def reload(self):
        for object in self._objects:
            object.reload()
    
    def add_in_view(self, view):
        for object in self._objects:
            view.add_object(object)
        
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
