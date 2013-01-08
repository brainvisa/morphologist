import os

import anatomist.direct.api as ana

from morphologist.gui.qt_backend import QtCore
from morphologist.backends import Backend
from morphologist.backends.mixins import DisplayManagerMixin, \
                                         ObjectsManagerMixin, LoadObjectError


class PyanatomistBackend(Backend, DisplayManagerMixin, ObjectsManagerMixin):
    anatomist = None
    
    def __new__(cls):
        if cls.anatomist is None:
            cls._init_anatomist()
        return super(PyanatomistBackend, cls).__new__(cls)
        
    def __init__(self):
        super(PyanatomistBackend, self).__init__()
        super(DisplayManagerMixin, self).__init__()
        super(ObjectsManagerMixin, self).__init__()

### display backend
    @classmethod
    def _init_anatomist(cls):
        cls.anatomist = ana.Anatomist("-b")

    @classmethod
    def add_object_in_view(cls, backend_object, backend_view):
        backend_view.addObjects(backend_object)

    @classmethod
    def clear_view(cls, backend_view):
        backend_view.removeObjects(backend_view.objects)
        

    @classmethod
    def set_bgcolor_view(cls, backend_view, rgba_color):
        cls.anatomist.execute('WindowConfig',
                windows=[backend_view], cursor_visibility=0,
                light={'background' : rgba_color})
    

    @classmethod
    def set_position(cls, backend_view, position):
        backend_view.moveLinkedCursor(position)
        
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

### objects loader backend    
    @classmethod
    def reload_object(cls, backend_object):
        backend_object.reload()
    
    @classmethod
    def shallow_copy_backend_object(cls, backend_object):
        return cls.anatomist.duplicateObject(backend_object)
        
    @classmethod
    def get_object_center_position(cls, backend_object):
        bb = backend_object.boundingbox()
        position = (bb[1] - bb[0]) / 2
        return position

    
    @classmethod
    def set_object_color_map(cls, backend_object, color_map_name):
        backend_object.setPalette(color_map_name)
    
    @classmethod
    def set_object_color(cls, backend_object, rgba_color):
        backend_object.setMaterial(diffuse=rgba_color)

    @classmethod
    def create_backend_fusion_object(cls, avol1, avol2, mode, rate):
        fusion = cls.anatomist.fusionObjects([avol1, avol2], method='Fusion2DMethod')
        cls.anatomist.execute("Fusion2DParams", object=fusion, mode=mode, rate=rate,
                              reorder_objects=[avol1, avol2])
        return fusion

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
