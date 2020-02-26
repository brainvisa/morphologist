from __future__ import absolute_import
from morphologist.core.gui.qt_backend import QtGui
from morphologist.core.backends import Backend
from morphologist.core.backends.mixins import DisplayManagerMixin, \
                                         ObjectsManagerMixin


class MockObjectDisplayBackend(Backend, DisplayManagerMixin, ObjectsManagerMixin):

    def __init__(self):
        super(MockObjectDisplayBackend, self).__init__()
        super(DisplayManagerMixin, self).__init__()
        super(ObjectsManagerMixin, self).__init__()

### display backend
    @classmethod
    def add_object_in_view(cls, backend_object, backend_view):
        pass

    @classmethod
    def clear_view(cls, backend_view):
        pass
        
    @classmethod
    def set_bgcolor_view(cls, backend_view, rgba_color):
        pass

    @classmethod
    def set_position(cls, backend_view, position):
        pass
        
    @classmethod
    def create_view(cls, parent, view_type):
        return QtGui.QWidget(parent)
        
### objects loader backend    
    @classmethod
    def reload_object(cls, backend_object):
        pass
    
    @classmethod
    def shallow_copy_object(cls, backend_object):
        return backend_object
        
    @classmethod
    def get_object_center_position(cls, backend_object):
        return [0, 0, 0]

    @classmethod
    def set_object_color_map(cls, backend_object, color_map_name):
        pass
    
    @classmethod
    def set_object_color(cls, backend_object, rgba_color):
        pass

    @classmethod
    def create_fusion_object(cls, backend_object1, backend_object2, mode, rate):
        return None

    @classmethod
    def load_object(cls, filename):
        return None
    
    @classmethod
    def create_point_object(cls, coordinates):
        return None        
        