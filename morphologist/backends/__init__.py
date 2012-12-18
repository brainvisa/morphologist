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

    def add_objects_to_window(self, objects, window):
        raise Exception("DisplayManagerMixin is an abstract class")

    def remove_objects_from_window(self, objects, window):
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


class ObjectsManagerMixin(object):

    def load_object(self, filename):
        raise Exception("ObjectsLoaderMixin is an abstract class")

    def reload_object_if_needed(self, object):
        raise Exception("ObjectsLoaderMixin is an abstract class")

    def delete_objects(self, objects):
        raise Exception("ObjectsLoaderMixin is an abstract class")

    def set_palette(self, palette_name):
        raise Exception("ObjectsLoaderMixin is an abstract class")

class LoadObjectError(Exception):
    pass
    
