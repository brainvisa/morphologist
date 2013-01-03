import os

import anatomist.direct.api as ana

from morphologist.gui.qt_backend import QtCore
from morphologist.backends import Backend
from morphologist.backends.mixins import DisplayManagerMixin, \
                                         ObjectsManagerMixin, LoadObjectError


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

    # this method should be used only by the View object ("friend" method)
    @classmethod
    def create_backend_view(cls, parent=None):
        wintype = 'Axial'
        cmd = ana.cpp.CreateWindowCommand(wintype, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        cls.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        return awindow

    @classmethod
    def add_object_in_view(cls, object, view):
        awindow = view.backend_view
        awindow.addObjects(object.backend_object)
   
    @classmethod
    def clear_view(cls, view):
        awindow = view.backend_view
        awindow.removeObjects(awindow.objects)

    @classmethod
    def set_bgcolor_view(cls, view, rgba_color):
        # rgba_color must a list of 4 floats between 0 and 1
        cls.anatomist.execute('WindowConfig',
                windows=[view.backend_view], cursor_visibility=0,
                light={'background' : rgba_color})
    
    @classmethod
    def set_position(cls, view, position):
        awindow = view.backend_view
        awindow.moveLinkedCursor(position)
        
### objects loader backend
    @classmethod
    def load_backend_object(cls, filename):
        aobject = cls.anatomist.loadObject(filename)
        if aobject.getInternalRep() == None:
            raise LoadObjectError(str(filename))
        return aobject
    
    @classmethod
    def create_backend_point_object(cls, coordinates):
        cross_mesh = os.path.join(cls.anatomist.anatomistSharedPath(), 
                                  "cursors", "cross.mesh")
        point_object = cls.anatomist.loadObject(cross_mesh, forceReload=True)
        referential = cls.anatomist.createReferential()
        point_object.assignReferential(referential)
        cls.anatomist.createTransformation(coordinates + [ 1, 0, 0,
                                                            0, 1, 0,
                                                            0, 0, 1 ], 
                                            referential, 
                                            cls.anatomist.centralRef)
        return point_object
    
    @classmethod
    def reload_object(cls, object):
        object.backend_object.reload()
    
    @classmethod
    def get_object_center_position(cls, object):
        aobject = object.backend_object
        bb = aobject.boundingbox()
        position = (bb[1] - bb[0]) / 2
        return position
    
    @classmethod
    def set_object_color_map(cls, object, color_map_name):
        object.backend_object.setPalette(color_map_name)
    
    @classmethod
    def set_object_color(cls, object, rgba_color):
        object.backend_object.setMaterial(diffuse = rgba_color)

