from morphologist.core import settings


class Format(object):
    def __init__(self, name):
        self.name = name
        self.extensions = []


class FormatsManager(object):
    _formats = []
    _formats_manager_instance = None
    _formats_backend_modules = {
    #   backend name : (backend module name, backend class name)
        'brainvisa' : ('morphologist.core.backends.brainvisa_backend',
                                        'BrainvisaFormatsManager')
    }

    @classmethod
    def formats(cls):
        if len(cls._formats) == 0:
            cls._fill_formats_and_extensions()
        return cls._formats

    @classmethod
    def _fill_formats_and_extensions(cls):
        raise NotImplementedError("FormatsManager is an abstract class")

    @classmethod
    def formats_manager(cls):
        if cls._formats_manager_instance:
            return cls._formats_manager_instance
        formats_manager_backend = settings['formats_manager_backend']
        backend_info = cls._formats_backend_modules[formats_manager_backend]
        modulename, classname = backend_info
        try:
            module = __import__(modulename, fromlist=classname)
            FormatsManagerBackend = module.__getattribute__(classname)
        except ImportError, e:
            raise ValueError("invalid format backend : '%s' (%s)" % \
                                        (formats_manager_backend, e))
        cls._formats_manager_instance = FormatsManagerBackend()
        return cls._formats_manager_instance

    @classmethod
    def available_formats_manager_backend(cls):
        return cls._formats_backend_modules.keys()
