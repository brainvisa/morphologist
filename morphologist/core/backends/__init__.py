from morphologist.core.settings import settings


class Backend(object):
    DISPLAY_ROLE = 'display'
    OBJECTS_LOADER_ROLE = 'objects'
    VECTOR_GRAPHICS_ROLE = 'vector_graphics'
    _backend_instance = {}
    _backend_loading_info = {
        'pyanatomist' : ('morphologist.core.backends.pyanatomist_backend',
                                                    'PyanatomistBackend'),
        'morphologist_common' : ('morphologist.core.backends.morphologist_common_backend', 'MorphologistCommonBackend'), 
        'mock_object_display' : ('morphologist.core.backends.mock_object_display_backend', 'MockObjectDisplayBackend')
    }

    @classmethod
    def display_backend(cls):
        return cls.backend_from_role(cls.DISPLAY_ROLE)

    @classmethod
    def objects_loader_backend(cls):
        return cls.backend_from_role(cls.OBJECTS_LOADER_ROLE)

    @classmethod
    def vector_graphics_backend(cls):
        return cls.backend_from_role(cls.VECTOR_GRAPHICS_ROLE)

    @classmethod
    def select_display_backend(cls, backend_name):
        cls.select_backend_from_role(cls.DISPLAY_ROLE)

    @classmethod
    def select_objects_loader_backend(cls, backend_name):
        cls.select_backend_from_role(cls.OBJECTS_LOADER_ROLE)

    @classmethod
    def select_vector_graphics_backend(cls, backend_name):
        cls.select_backend_from_role(cls.VECTOR_GRAPHICS_ROLE)

    @classmethod
    def backend_from_role(cls, role):
        try:
            instance = cls._backend_instance[role]
        except KeyError:
            backend_name = settings.backends.__getattr__(role)
            cls.select_backend_from_role(role, backend_name)
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

