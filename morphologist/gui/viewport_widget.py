import os

from morphologist.backends import Backend
from morphologist.backends.mixins import LoadObjectError
from morphologist.gui.object3d import Object3D, APCObject, View
from morphologist.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.gui import ui_directory 
from morphologist.intra_analysis import IntraAnalysis


class AnalysisViewportModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self, model):
        super(AnalysisViewportModel, self).__init__()
        self._init_model(model)
        self._init_3d_objects()

    def _init_model(self, model):
        self._analysis_model = model
        self._analysis_model.changed.connect(self.on_analysis_model_changed)
        self._analysis_model.files_changed.connect(\
                self.on_analysis_model_files_changed)

    def _init_3d_objects(self):
        raise Exception("SubjectwiseViewportModel is an abstract class")

    @QtCore.Slot()
    def on_analysis_model_changed(self):
        # XXX : may need a cache ?
        self._init_3d_objects()
        self.changed.emit()

    @QtCore.Slot(dict)
    def on_analysis_model_files_changed(self, changed_parameters):
        for parameter_name, filename in changed_parameters.items():
            if not parameter_name in self.observed_objects.keys():
                continue
            object = self.observed_objects[parameter_name]
            if object is not None:
                if os.path.exists(filename):
                    object.reload()
                else:
                    object = None
            else:
                try:
                    object = self.load_object(parameter_name, filename)
                except LoadObjectError, e:
                    object = None
            self.observed_objects[parameter_name] = object
            signal = self.signal_map.get(parameter_name)
            if signal is not None:
                self.__getattribute__(signal).emit()

    @classmethod
    def load_object(cls, parameter_name, filename):
        return Object3D(filename)


class IntraAnalysisViewportModel(AnalysisViewportModel):
    changed = QtCore.pyqtSignal()
    raw_mri_changed = QtCore.pyqtSignal()
    commissure_coordinates_changed = QtCore.pyqtSignal()
    corrected_mri_changed = QtCore.pyqtSignal()
    brain_mask_changed = QtCore.pyqtSignal()
    split_mask_changed = QtCore.pyqtSignal()
    signal_map = { \
        IntraAnalysis.MRI : 'raw_mri_changed',
        IntraAnalysis.COMMISSURE_COORDINATES : 'commissure_coordinates_changed',
        IntraAnalysis.CORRECTED_MRI : 'corrected_mri_changed',
        IntraAnalysis.BRAIN_MASK : 'brain_mask_changed',
        IntraAnalysis.SPLIT_MASK : 'split_mask_changed'
    }

    def __init__(self, model):
        super(IntraAnalysisViewportModel, self).__init__(model)

    def _init_3d_objects(self):
        self.observed_objects = { \
            IntraAnalysis.MRI : None,
            IntraAnalysis.COMMISSURE_COORDINATES : None, 
            IntraAnalysis.CORRECTED_MRI : None,
            IntraAnalysis.BRAIN_MASK : None,
            IntraAnalysis.SPLIT_MASK : None
        }

    @classmethod
    def load_object(cls, parameter_name, filename):
        obj = None
        if (parameter_name == IntraAnalysis.COMMISSURE_COORDINATES):
            obj = APCObject(filename)
        else:
            obj = Object3D(filename) 
        return obj


class IntraAnalysisViewportView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'viewport_widget.ui')
    main_frame_style_sheet = '''
        #viewport_frame { background-color: white }
        #view1_frame, #view2_frame, #view3_frame, #view4_frame {
            border: 3px solid black;
            border-radius: 20px;
            background: black;
        }
        #view1_label, #view2_label, #view3_label, #view4_label {
            color: white;
        }
    '''

    def __init__(self, parent=None):
        super(IntraAnalysisViewportView, self).__init__(parent)
        self.ui = loadUi(self.uifile, parent)
        self._views = []
        self._viewport_model = None
        Backend.display_backend().initialize_display()
        self._init_widget()

    def set_model(self, model):
        if self._viewport_model is not None:
            self._viewport_model.changed.disconnect(self.on_model_changed)
            self._viewport_model.raw_mri_changed.disconnect(\
                                    self.on_raw_mri_changed)
            self._viewport_model.commissure_coordinates_changed.disconnect(\
                                        self.on_commissure_coordinates_changed)
            self._viewport_model.corrected_mri_changed.disconnect(\
                                    self.on_corrected_mri_changed)
            self._viewport_model.brain_mask_changed.disconnect(\
                                    self.on_brain_mask_changed)
            self._viewport_model.split_mask_changed.disconnect(\
                                    self.on_split_mask_changed)
        self._viewport_model = model
        self._viewport_model.changed.connect(self.on_model_changed)
        self._viewport_model.raw_mri_changed.connect(self.on_raw_mri_changed)
        self._viewport_model.commissure_coordinates_changed.connect(self.on_commissure_coordinates_changed)
        self._viewport_model.corrected_mri_changed.connect(self.on_corrected_mri_changed)
        self._viewport_model.brain_mask_changed.connect(self.on_brain_mask_changed)
        self._viewport_model.split_mask_changed.connect(self.on_split_mask_changed)

    def _init_widget(self):
        self.ui.setStyleSheet(self.main_frame_style_sheet)
        for view_hook in [self.ui.view1_hook, self.ui.view2_hook, 
                          self.ui.view3_hook, self.ui.view4_hook]:
            QtGui.QVBoxLayout(view_hook)
            view = View(view_hook)
            view.set_bgcolor([0., 0., 0., 1.])
            self._views.append(view)
        self.view1, self.view2, self.view3, self.view4 = self._views
        
    @QtCore.Slot()
    def on_model_changed(self):
        for view in self._views:
            view.clear()

    @QtCore.Slot()
    def on_raw_mri_changed(self):
        object = self._viewport_model.observed_objects[IntraAnalysis.MRI]
        if object is not None:
            self.view1.add_object(object)
            self.view1.center_on_object(object)

    @QtCore.Slot()
    def on_commissure_coordinates_changed(self):
        apc_object = self._viewport_model.observed_objects[IntraAnalysis.COMMISSURE_COORDINATES]
        if apc_object is not None:
            apc_object.set_ac_color(( 0, 0, 1, 1 )) 
            apc_object.set_pc_color(( 1, 1, 0, 1 )) 
            apc_object.set_ih_color(( 0, 1, 0, 1 ))
            self.view1.add_object(apc_object)
            self.view1.center_on_object(apc_object)

    @QtCore.Slot()
    def on_corrected_mri_changed(self):
        object = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
        if object is not None:
            object.set_color_map("Rainbow2")
            self.view2.add_object(object)

    @QtCore.Slot()
    def on_brain_mask_changed(self):
        object = self._viewport_model.observed_objects[IntraAnalysis.BRAIN_MASK]
        if object is not None:
            object.set_color_map("GREEN-lfusion")
            self.view3.add_object(object)

    @QtCore.Slot()
    def on_split_mask_changed(self):
        object = self._viewport_model.observed_objects[IntraAnalysis.SPLIT_MASK]
        if object is not None:
            object.set_color_map("RAINBOW")
            self.view4.add_object(object)

     
