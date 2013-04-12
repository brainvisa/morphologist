import os

import anatomist.direct.api as ana
from soma import aims

from morphologist.core.gui.qt_backend import QtCore
from morphologist.core.backends import Backend
from morphologist.core.backends.mixins import DisplayManagerMixin, \
                                         ObjectsManagerMixin, LoadObjectError, \
                                         ColorMap, ViewType


class PyanatomistBackend(Backend, DisplayManagerMixin, ObjectsManagerMixin):
    anatomist = None
    sulci_color_map = None
    color_map_names = {ColorMap.RAINBOW_MASK : "RAINBOW", 
                       ColorMap.GREEN_MASK : "GREEN-lfusion",
                       ColorMap.RAINBOW : "Rainbow2"}
    
    def __new__(cls):
        if cls.anatomist is None:
            cls._init_anatomist()
        if cls.sulci_color_map is None:
            cls.sulci_color_map = cls._load_sulci_color_map()
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
    def reset_view_camera(self, backend_view):
        if backend_view.windowType == ViewType.AXIAL:
            backend_view.internalRep.muteAxial()
        elif backend_view.windowType == ViewType.CORONAL:
            backend_view.internalRep.muteCoronal()
        elif backend_view.windowType == ViewType.SAGITTAL:
            backend_view.internalRep.muteSagittal()
        elif backend_view.windowType == ViewType.THREE_D:
            backend_view.internalRep.mute3D()
        backend_view.camera(zoom=1)
        
    @classmethod
    def set_bgcolor_view(cls, backend_view, rgba_color):
        cls.anatomist.execute('WindowConfig',
                windows=[backend_view], cursor_visibility=0,
                light={'background' : rgba_color})
    

    @classmethod
    def set_position(cls, backend_view, position):
        backend_view.moveLinkedCursor(position)
        
    @classmethod
    def create_view(cls, parent, view_type):
        cmd = ana.cpp.CreateWindowCommand(view_type, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        cls.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        if view_type == ViewType.THREE_D:
            awindow.camera(zoom=1.5, 
                           view_quaternion=[0.558559238910675,0.141287177801132,\
                                            0.196735754609108,0.793312430381775])
        return awindow

### objects loader backend    
    @classmethod
    def reload_object(cls, backend_object):
        backend_object.reload()
    
    @classmethod
    def shallow_copy_object(cls, backend_object):
        return cls.anatomist.duplicateObject(backend_object)
        
    @classmethod
    def get_object_center_position(cls, backend_object):
        bb = backend_object.boundingbox()
        position = (bb[1] - bb[0]) / 2
        return position

    @classmethod
    def set_object_color_map(cls, backend_object, color_map_name):
        backend_object.setPalette(cls.color_map_names.get(color_map_name))
    
    @classmethod
    def set_object_color(cls, backend_object, rgba_color):
        backend_object.setMaterial(diffuse=rgba_color)

    @classmethod
    def create_fusion_object(cls, backend_object1, backend_object2, mode, rate):
        fusion = cls.anatomist.fusionObjects([backend_object1, backend_object2], 
                                             method='Fusion2DMethod')
        cls.anatomist.execute("TexturingParams", objects=[fusion], mode=mode, rate=rate, 
                              texture_index=1)
        return fusion

    @classmethod
    def load_object(cls, filename):
        aobject = cls.anatomist.loadObject(filename)
        if aobject.getInternalRep() == None:
            raise LoadObjectError(str(filename))
        return aobject
    
    @classmethod
    def create_point_object(cls, coordinates):
        cross_name = os.path.join(cls.anatomist.anatomistSharedPath(), 
                                  "cursors", "cross.mesh")
        cross_mesh = aims.read(cross_name)
        motion = aims.Motion()
        motion.setTranslation(coordinates)
        aims.SurfaceManip.meshTransform(cross_mesh, motion)
        cross_object = cls.anatomist.toAObject(cross_mesh)
        cross_object.releaseAppRef()
        return cross_object

    @classmethod
    def _load_sulci_color_map(cls):
        anatomist_shared_path = unicode(cls.anatomist.anatomistSharedPath())
        shared_dirname = os.path.dirname(anatomist_shared_path)
        shared_basename = os.path.basename(anatomist_shared_path)
        brainvisa_share = shared_basename.replace("anatomist", "brainvisa-share")
        brainvisa_share_path = os.path.join(shared_dirname, brainvisa_share)
        sulci_colormap_filename = os.path.join(brainvisa_share_path, "nomenclature", 
                                               "hierarchy", "sulcal_root_colors.hie")
        cls.anatomist.execute("GraphParams", label_attribute="label")
        return cls.load_object(sulci_colormap_filename) 
        
        