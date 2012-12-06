import os

import anatomist.direct.api as ana

from morphologist.gui.qt_backend import QtCore
from morphologist.backends import Backend, \
            DisplayManagerMixin, ObjectsManagerMixin


class PyanatomistBackend(Backend, DisplayManagerMixin, ObjectsManagerMixin):

    def __init__(self):
        super(PyanatomistBackend, self).__init__()
        super(DisplayManagerMixin, self).__init__()
        super(ObjectsManagerMixin, self).__init__()

### display backend
    def initialize_display(self):
        # must be call after the Qt eventloop has been started
        self.__class__.anatomist = ana.Anatomist('-b')

    def create_axial_view(self, parent=None):
        wintype = 'Axial'
        cmd = ana.cpp.CreateWindowCommand(wintype, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        self.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        awindow = self.anatomist.AWindow(self.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        return window

    def add_objects_to_window(self, objects, window):
        awindow = self.anatomist.AWindow(self.anatomist, window)
        awindow.addObjects(objects)

    def remove_objects_from_window(self, objects, window):
        awindow = self.anatomist.AWindow(self.anatomist, window)
        awindow.removeObjects(objects)

    def clear_window(self, window):
        awindow = self.anatomist.AWindow(self.anatomist, window)
        awindow.removeObjects(awindow.objects)
        
    def clear_windows(self, windows):
        for window in windows:
            self.clear_window(window)
        
    def center_window_on_object(self, window, object):
        bb = object.boundingbox()
        position = (bb[1] - bb[0]) / 2
        awindow = self.anatomist.AWindow(self.anatomist, window)
        awindow.moveLinkedCursor(position)

    def set_bgcolor_views(self, views, rgba_color):
        # rgba_color must a list of 4 floats between 0 and 1
        self.anatomist.execute('WindowConfig',
                windows=views, cursor_visibility=0,
                light={'background' : rgba_color})

### objects loader backend
    def load_object(self, filename):
        object = self.anatomist.loadObject(filename)
        return object

    def reload_object(self, object):
        object.reload()
        return object

    def reload_object_if_needed(self, object):
        filename = object.fileName()
        if os.path.exists(filename):
            object.reload()
            return object
        else:
            return None
        
    def delete_objects(self, objects):
        return self.anatomist.deleteObjects(objects)
