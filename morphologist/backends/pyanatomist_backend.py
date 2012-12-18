import os

import anatomist.direct.api as ana

from morphologist.gui.qt_backend import QtCore
from morphologist.backends import Backend, \
            DisplayManagerMixin, ObjectsManagerMixin, \
            LoadObjectError, Object3DMixin
            

class PyanatomistBackend(Backend, DisplayManagerMixin, ObjectsManagerMixin):

    def __init__(self):
        super(PyanatomistBackend, self).__init__()
        super(DisplayManagerMixin, self).__init__()
        super(ObjectsManagerMixin, self).__init__()

### display backend
    @classmethod
    def initialize_display(cls):
        # must be call after the Qt eventloop has been started
        cls.anatomist = ana.Anatomist("-b")

    @classmethod
    def create_axial_view(cls, parent=None):
        wintype = 'Axial'
        cmd = ana.cpp.CreateWindowCommand(wintype, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        cls.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        return window

    @classmethod
    def add_object_to_window(cls, object, window):
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        awindow.addObjects(object.aobject)

    @classmethod
    def remove_object_from_window(cls, object, window):
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        awindow.removeObjects(object.aobject)

    @classmethod
    def clear_window(cls, window):
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        awindow.removeObjects(awindow.objects)
        
    @classmethod
    def clear_windows(cls, windows):
        for window in windows:
            cls.clear_window(window)
        
    @classmethod
    def center_window_on_object(cls, window, object):
        aobject = object.aobject
        bb = aobject.boundingbox()
        position = (bb[1] - bb[0]) / 2
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        awindow.moveLinkedCursor(position)

    @classmethod
    def set_bgcolor_views(cls, views, rgba_color):
        # rgba_color must a list of 4 floats between 0 and 1
        cls.anatomist.execute('WindowConfig',
                windows=views, cursor_visibility=0,
                light={'background' : rgba_color})

    @classmethod
    def move_cursor(cls, window, position):
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        awindow.moveLinkedCursor(position)
        
### objects loader backend
    @classmethod
    def load_object(cls, filename):
        aobject = cls.anatomist.loadObject(filename)
        if aobject.getInternalRep() == None:
            raise LoadObjectError(str(filename))
        object = PyanatomistObject3D(filename, aobject)
        return object
    

class PyanatomistObject3D(Object3DMixin):
    
    def __init__(self, filename, aobject):
        super(PyanatomistObject3D, self).__init__(filename)
        self.aobject = aobject

    def reload(self):
        self.aobject.reload()
        return self
    
    def set_color_map(self, color_map_name):
        self.aobject.setPalette(color_map_name)
    
    def set_color(self, rgba_color):
        self.aobject.setMaterial(diffuse = rgba_color)
        
