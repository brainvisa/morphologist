from morphologist.core.backends import Backend
from morphologist.core.utils.design_patterns import Visitable


class VectorObject(Visitable):
    
    def __init__(self):
        self._backend = Backend.vector_graphics_backend()
        self._friend_backend_object = None

    def _friend_accept_visitor(self, visitor):
        visitor._friend_visit(self)
        
    
class Histogram(VectorObject):
    
    def __init__(self, _enable_init=False):
        super(Histogram, self).__init__()
        if not _enable_init:
            raise Exception("Default constructor not allowed, use from_* static methods instead.")
     
    @classmethod
    def from_filename(cls, filename):
        print 'load histo:', filename
        vector_graphic = cls(_enable_init=True)
        vector_graphic._friend_backend_object \
            = vector_graphic._backend.load_histogram(filename)
        return vector_graphic

    def reload(self):
        print 'reload histo:', self._friend_backend_object.han_filename
        _friend_backend_object \
            = self.__class__.from_filename(
                self._friend_backend_object.han_filename)


class VectorView(object):
    
    def __init__(self, parent):
        self._backend = Backend.vector_graphics_backend()
        self._backend_view = self._backend.create_view(parent)
        
    def add_object(self, vector_graphic):
        vector_graphic._friend_accept_visitor(self)
                
    def clear(self):
        self._backend.clear_view(self._backend_view)
    
    def set_bgcolor(self, color):
        self._backend.set_bgcolor_view(self._backend_view, color)
        
    def _friend_visit(self, vector_graphic):
        self._backend.add_object_in_view(vector_graphic._friend_backend_object, self._backend_view)


class VectorExtendedView(object):

    def __init__(self, parent):
        self._backend = Backend.vector_graphics_backend()
        self._backend_view = self._backend.create_extended_view(parent)

    def add_object(self, vector_graphic):
        vector_graphic._friend_accept_visitor(self)

    def clear(self):
        self._backend.clear_view(self._backend_view)

    def set_bgcolor(self, color):
        self._backend.set_bgcolor_editor(self._backend_view, color)

    def _friend_visit(self, vector_graphic):
        self._backend.add_object_in_editor(vector_graphic._friend_backend_object, self._backend_view)
