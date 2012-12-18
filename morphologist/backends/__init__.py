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

    def create_axial_view(self, parent=None):
        raise Exception("DisplayManagerMixin is an abstract class")

    def add_object_to_window(self, object, window):
        raise Exception("DisplayManagerMixin is an abstract class")

    def remove_object_from_window(self, object, window):
        raise Exception("DisplayManagerMixin is an abstract class")
   
    def clear_window(self, window):
        raise Exception("DisplayManagerMixin is an abstract class")
    
    def clear_windows(self, windows):
        for window in windows:
            self.clear_window(window)
        
    def center_window_on_object(self, window, object):
        raise Exception("DisplayManagerMixin is an abstract class")

    def set_bgcolor_views(self, views, rgba_color):
        raise Exception("DisplayManagerMixin is an abstract class")
    
    def move_cursor(self, window, position):
        raise Exception("DisplayManagerMixin is an abstract class")


class ObjectsManagerMixin(object):

    def load_object(self, filename):
        raise Exception("ObjectsLoaderMixin is an abstract class")


class LoadObjectError(Exception):
    pass

class Object3DMixin(object):
    
    def __init__(self, filename):
        self.filename = filename

    def reload(self):
        raise Exception("Object3DMixin is an abstract class")
    
    def set_color_map(self, color_map_name):
        raise Exception("Object3DMixin is an abstract class")
    
    def set_color(self, rgba_color):
        raise Exception("Object3DMixin is an abstract class")

        
class ObjectAPCMixin(Object3DMixin):
    
    def __init__(self, filename):
        super(ObjectAPCMixin, self).__init__(filename)
        self.ac_coordinates = None
        self.pc_coordinates = None
        self.ih_coordinates = None
        self.ac_object = None
        self.pc_object = None
        self.ih_object = None
        self._init_coordinates()
        
    def _init_coordinates(self):
        apcfile = open(self.filename, "r")
        lines = apcfile.readlines()
        for l in lines:
            if l[:5] == 'ACmm:':
                self.ac_coordinates = map( lambda x: float(x), l.split()[1:4] )
            elif l[:5] == 'PCmm:':
                self.pc_coordinates = map( lambda x: float(x), l.split()[1:4] )
            elif l[:5] == 'IHmm:':
                self.ih_coordinates = map( lambda x: float(x), l.split()[1:4] )

    def get_points_objects(self):
        return (self.ac_object, self.pc_object, self.ih_object)
    
    def set_color(self, rgba_color):
        for object in (self.ac_object, self.pc_object, self.ih_object):
            if object is not None:
                object.set_color(rgba_color)
                
    def set_color_map(self, color_map_name):
        for object in (self.ac_object, self.pc_object, self.ih_object):
            if object is not None:
                object.set_color_map(color_map_name)
