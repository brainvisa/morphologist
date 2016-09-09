import os
import sys

import anatomist.direct.api as ana
from anatomist.cpp.simplecontrols import Simple2DControl, Simple3DControl, \
    registerSimpleControls
from soma import aims

from morphologist.core.gui.qt_backend import QtCore, QtGui
from morphologist.core.backends import Backend
from morphologist.core.backends.mixins \
    import DisplayManagerMixin, ObjectsManagerMixin, LoadObjectError, \
        ColorMap, ViewType

if sys.version_info[0] >= 3:
    unicode = str


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
        cls._init_view_controls()

    @classmethod
    def _init_view_controls(cls):
        # register controls
        registerSimpleControls()
        control_manager = ana.cpp.ControlManager.instance()
        control_manager.addControl( 'QAGLWidget3D', '', 'Simple2DControl' )
        control_manager.addControl( 'QAGLWidget3D', '', 'Simple3DControl' )

    @classmethod
    def add_object_in_view(cls, backend_object, backend_view):
        backend_view.addObjects(backend_object)

    @classmethod
    def clear_view(cls, backend_view):
        backend_view.removeObjects(backend_view.objects)

    @classmethod
    def reset_view_camera(cls, backend_view):
        cls.set_view_type(backend_view, backend_view.windowType)
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
    def create_view(cls, parent, view_type, restricted_controls=True):
        cmd = ana.cpp.CreateWindowCommand(view_type, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        cls.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        window.setAcceptDrops( False )
        awindow = cls.anatomist.AWindow(cls.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        if view_type == ViewType.THREE_D:
            control = "Simple3DControl"
            awindow.camera(
                zoom=1.5,
                view_quaternion=[0.558559238910675,0.141287177801132,\
                                 0.196735754609108,0.793312430381775])
        else:
            control = 'Simple2DControl'
        if restricted_controls:
            cls.anatomist.execute( 'SetControl', windows=[awindow], control=control )
        return awindow

    @classmethod
    def get_view_type(cls, backend_view):
        return backend_view.windowType

    @classmethod
    def set_view_type(cls, backend_view, view_type):
        if view_type == ViewType.AXIAL:
            backend_view.internalRep.muteAxial()
        elif view_type == ViewType.CORONAL:
            backend_view.internalRep.muteCoronal()
        elif view_type == ViewType.SAGITTAL:
            backend_view.internalRep.muteSagittal()
        elif view_type == ViewType.THREE_D:
            backend_view.internalRep.mute3D()

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
    def set_object_color_map(cls, backend_object, color_map_name, min=None,
                             max=None):
        backend_object.setPalette(
            cls.color_map_names.get(color_map_name), minVal=min,
            maxVal=max, absoluteMode=True)

    @classmethod
    def set_object_color(cls, backend_object, rgba_color):
        backend_object.setMaterial(diffuse=rgba_color)

    @classmethod
    def create_fusion_object(cls, backend_objects, mode=None,
                             rate=None, method=None):
        if method is None:
            method = 'Fusion2DMethod'
        fusion = cls.anatomist.fusionObjects(backend_objects, method=method)
        if method == 'Fusion2DMethod' and mode is not None \
                and method is not None:
            cls.anatomist.execute("TexturingParams", objects=[fusion],
                                  mode=mode, rate=rate, texture_index=1)
        return fusion

    @classmethod
    def load_object(cls, filename):
        QtGui.qApp.setOverrideCursor(QtCore.Qt.WaitCursor)
        aobject = cls.anatomist.loadObject(filename)
        QtGui.qApp.restoreOverrideCursor()
        if aobject.getInternalRep() == None:
            raise LoadObjectError(str(filename))
        return aobject

    @classmethod
    def load_object_async(cls, filename, callback):
        cls.anatomist.loadObject(filename, asyncCallback=callback)

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
