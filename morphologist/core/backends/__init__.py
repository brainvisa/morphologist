from morphologist.core import settings


class Backend(object):
    DISPLAY_ROLE = 'display_backend'
    OBJECTS_LOADER_ROLE = 'objects_backend'
    _backend_instance = {}
    _backend_loading_info = {
        'pyanatomist' : ('morphologist.core.backends.pyanatomist_backend',
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
            cls.select_backend_from_role(role, settings[role])
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

