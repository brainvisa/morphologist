import os

from morphologist_common import histo_analysis_widget

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
        raise NotImplementedError("SubjectwiseViewportModel is an abstract class")

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
        return Object3D.from_filename(filename)


class IntraAnalysisViewportModel(AnalysisViewportModel):
    changed = QtCore.pyqtSignal()
    raw_mri_changed = QtCore.pyqtSignal()
    commissure_coordinates_changed = QtCore.pyqtSignal()
    corrected_mri_changed = QtCore.pyqtSignal()
    histo_analysis_changed = QtCore.pyqtSignal()
    brain_mask_changed = QtCore.pyqtSignal()
    split_mask_changed = QtCore.pyqtSignal()
    grey_white_changed = QtCore.pyqtSignal()
    grey_surface_changed = QtCore.pyqtSignal()
    white_surface_changed = QtCore.pyqtSignal()

    signal_map = { \
        IntraAnalysis.MRI : 'raw_mri_changed',
        IntraAnalysis.COMMISSURE_COORDINATES : 'commissure_coordinates_changed',
        IntraAnalysis.CORRECTED_MRI : 'corrected_mri_changed',
        IntraAnalysis.HISTO_ANALYSIS : 'histo_analysis_changed',
        IntraAnalysis.BRAIN_MASK : 'brain_mask_changed',
        IntraAnalysis.SPLIT_MASK : 'split_mask_changed',
        IntraAnalysis.LEFT_GREY_WHITE : 'grey_white_changed',
        IntraAnalysis.RIGHT_GREY_WHITE : 'grey_white_changed',
        IntraAnalysis.LEFT_GREY_SURFACE : 'grey_surface_changed', 
        IntraAnalysis.RIGHT_GREY_SURFACE : 'grey_surface_changed', 
        IntraAnalysis.LEFT_WHITE_SURFACE : 'white_surface_changed',
        IntraAnalysis.RIGHT_WHITE_SURFACE : 'white_surface_changed'
    }

    def __init__(self, model):
        super(IntraAnalysisViewportModel, self).__init__(model)

    def _init_3d_objects(self):
        self.observed_objects = { \
            IntraAnalysis.MRI : None,
            IntraAnalysis.COMMISSURE_COORDINATES : None, 
            IntraAnalysis.CORRECTED_MRI : None,
            IntraAnalysis.HISTO_ANALYSIS : None,
            IntraAnalysis.BRAIN_MASK : None,
            IntraAnalysis.SPLIT_MASK : None,
            IntraAnalysis.LEFT_GREY_WHITE : None,
            IntraAnalysis.RIGHT_GREY_WHITE : None,
            IntraAnalysis.LEFT_GREY_SURFACE : None,
            IntraAnalysis.RIGHT_GREY_SURFACE : None,
            IntraAnalysis.LEFT_WHITE_SURFACE : None,
            IntraAnalysis.RIGHT_WHITE_SURFACE : None
        }

    @classmethod
    def load_object(cls, parameter_name, filename):
        obj = None
        if (parameter_name == IntraAnalysis.COMMISSURE_COORDINATES):
            obj = APCObject(filename)
        elif (parameter_name == IntraAnalysis.HISTO_ANALYSIS):
            obj = histo_analysis_widget.load_histo_data(filename)
        else:
            obj = Object3D.from_filename(filename) 
        return obj


class IntraAnalysisViewportView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'viewport_widget.ui')
    main_frame_style_sheet = '''
        #viewport_frame { background-color: white }
        #view1_frame, #view2_frame, #view3_frame, #view4_frame, #view5_frame, 
        #view6_frame, #view7_frame, #view8_frame {
            border: 3px solid black;
            border-radius: 20px;
            background: black;
       }
        #view1_label, #view2_label, #view3_label, #view4_label, #view5_label, 
        #view6_label, #view7_label, #view8_label {
            color: white;
        }
    '''
    RAW_MRI_ACPC = "raw_mri_acpc"
    BIAS_CORRECTED = "bias_corrected"
    HISTO_ANALYSIS="histo_analysis"
    BRAIN_MASK = "brain_mask"
    SPLIT_MASK = "split_mask"
    GREY_WHITE = "grey_white"
    GREY_SURFACE = "grey_surface"
    WHITE_SURFACE_SULCI = "white_surface_sulci"
    
    def __init__(self, model, parent=None):
        super(IntraAnalysisViewportView, self).__init__(parent)
        self.ui = loadUi(self.uifile, parent)
        self._views = {}
        self._objects = {}
        self._init_widget()
        self._init_model(model)

    def _init_model(self, model):
        self._viewport_model = model
        self._viewport_model.changed.connect(self.on_model_changed)
        self._viewport_model.raw_mri_changed.connect(self.update_raw_mri_acpc_view)
        self._viewport_model.commissure_coordinates_changed.connect(self.update_raw_mri_acpc_view)
        self._viewport_model.corrected_mri_changed.connect(self.update_corrected_mri_view) 
        self._viewport_model.corrected_mri_changed.connect(self.update_brain_mask_view) 
        self._viewport_model.corrected_mri_changed.connect(self.update_split_mask_view) 
        self._viewport_model.corrected_mri_changed.connect(self.update_grey_white_view) 
        self._viewport_model.corrected_mri_changed.connect(self.update_white_surface_sulci_view) 
        self._viewport_model.histo_analysis_changed.connect(self.update_histo_analysis_view)
        self._viewport_model.brain_mask_changed.connect(self.update_brain_mask_view)
        self._viewport_model.split_mask_changed.connect(self.update_split_mask_view)
        self._viewport_model.grey_white_changed.connect(self.update_grey_white_view)
        self._viewport_model.white_surface_changed.connect(self.update_grey_surface_view)
        self._viewport_model.white_surface_changed.connect(self.update_white_surface_sulci_view)

    def _init_widget(self):
        self.ui.setStyleSheet(self.main_frame_style_sheet)
        self.ui.view1_label.setText("1 ) Raw MRI + Anterior/posterior commissures")
        self.ui.view2_label.setText("2 ) Bias corrected MRI")
        self.ui.view3_label.setText("3 ) Histogram analysis")
        self.ui.view4_label.setText("4 ) Brain mask")
        self.ui.view5_label.setText("5 ) Cerebellum and hemispheres ")
        self.ui.view6_label.setText("6 ) Grey/White classification")
        self.ui.view7_label.setText("7 ) Grey surface")
        self.ui.view8_label.setText("8 ) White surface + Sulci")

        for view_name, view_hook in [(self.RAW_MRI_ACPC, self.ui.view1_hook), 
                                     (self.BIAS_CORRECTED, self.ui.view2_hook),
                                     (self.BRAIN_MASK, self.ui.view4_hook), 
                                     (self.SPLIT_MASK, self.ui.view5_hook),
                                     (self.GREY_WHITE, self.ui.view6_hook),
                                     (self.GREY_SURFACE, self.ui.view7_hook),
                                     (self.WHITE_SURFACE_SULCI, self.ui.view8_hook)]:
            QtGui.QVBoxLayout(view_hook)
            view = View(view_hook)
            view.set_bgcolor([0., 0., 0., 1.])
            self._views[view_name] = view
        QtGui.QVBoxLayout(self.ui.view3_hook)
        view = histo_analysis_widget.create_histo_view(self.ui.view3_hook)
        self._views[self.HISTO_ANALYSIS] = view

    @QtCore.Slot()
    def on_model_changed(self):
        for view in self._views.values():
            view.clear()

    @QtCore.Slot()
    def update_raw_mri_acpc_view(self):
        view = self._views[self.RAW_MRI_ACPC]
        view.clear()
        mri = self._viewport_model.observed_objects[IntraAnalysis.MRI]
        if mri is not None:
            view.add_object(mri)
            view.center_on_object(mri)
        apc_object = self._viewport_model.observed_objects[IntraAnalysis.COMMISSURE_COORDINATES]
        if apc_object is not None:
            apc_object.set_ac_color(( 0, 0, 1, 1 )) 
            apc_object.set_pc_color(( 1, 1, 0, 1 )) 
            apc_object.set_ih_color(( 0, 1, 0, 1 ))
            view.add_object(apc_object)
            view.center_on_object(apc_object)

    @QtCore.Slot()
    def update_corrected_mri_view(self):
        view = self._views[self.BIAS_CORRECTED]
        view.clear()
        corrected_mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
        if corrected_mri is not None:
            mri_copy = corrected_mri.shallow_copy()
            self._objects[self.BIAS_CORRECTED] = mri_copy
            mri_copy.set_color_map("Rainbow2")
            view.add_object(mri_copy)

    @QtCore.Slot()
    def update_histo_analysis_view(self):
        view = self._views[self.HISTO_ANALYSIS]
        histo_analysis = self._viewport_model.observed_objects[IntraAnalysis.HISTO_ANALYSIS]
        if histo_analysis is not None:
            view.set_histo_data(histo_analysis, nbins=100)
            view.draw_histo()

    @QtCore.Slot()
    def update_brain_mask_view(self):
        view = self._views[self.BRAIN_MASK]
        view.clear()
        mask = self._viewport_model.observed_objects[IntraAnalysis.BRAIN_MASK]
        if mask is not None:
            mask.set_color_map("GREEN-lfusion")
            mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(mri, mask, mode='linear', rate=0.7)
                self._objects[self.BRAIN_MASK] = fusion
                view.add_object(fusion)
            else:
                view.add_object(mask) 

    @QtCore.Slot()
    def update_split_mask_view(self):
        view = self._views[self.SPLIT_MASK]
        view.clear()
        mask = self._viewport_model.observed_objects[IntraAnalysis.SPLIT_MASK]
        if mask is not None:
            mask.set_color_map("RAINBOW")
            mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(mri, mask, mode='linear', rate=0.7)
                self._objects[self.SPLIT_MASK] = fusion
                view.add_object(fusion)
            else:
                view.add_object(mask) 


    @QtCore.Slot()
    def update_grey_white_view(self):
        view = self._views[self.GREY_WHITE]
        view.clear()
        left_mask = self._viewport_model.observed_objects[IntraAnalysis.LEFT_GREY_WHITE]
        right_mask = self._viewport_model.observed_objects[IntraAnalysis.RIGHT_GREY_WHITE]
        if left_mask is not None and right_mask is not None:
            left_mask.set_color_map("RAINBOW")
            right_mask.set_color_map("RAINBOW")
            mask_fusion = Object3D.from_fusion(left_mask, right_mask, mode='linear', rate=0.5)
            mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(mri, mask_fusion, mode='linear', rate=0.7)
                self._objects[self.GREY_WHITE] = fusion
                view.add_object(fusion)
            else:
                self._objects[self.GREY_WHITE] = mask_fusion
                view.add_object(mask_fusion)

    @QtCore.Slot()
    def update_grey_surface_view(self):
        view = self._views[self.GREY_SURFACE]
        view.clear()
        left_mesh = self._viewport_model.observed_objects[IntraAnalysis.LEFT_GREY_SURFACE]
        right_mesh = self._viewport_model.observed_objects[IntraAnalysis.RIGHT_GREY_SURFACE]
        yellow_color = [0.9, 0.7, 0.0, 1]
        if left_mesh is not None:
            left_mesh.set_color(yellow_color) 
            view.add_object(left_mesh)
        if right_mesh is not None:
            right_mesh.set_color(yellow_color)
            view.add_object(right_mesh)
        if left_mesh is not None or right_mesh is not None:
            mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
            if mri is not None:
                view.add_object(mri)

    @QtCore.Slot()
    def update_white_surface_sulci_view(self):
        view = self._views[self.WHITE_SURFACE_SULCI]
        view.clear()
        left_mesh = self._viewport_model.observed_objects[IntraAnalysis.LEFT_WHITE_SURFACE]
        right_mesh = self._viewport_model.observed_objects[IntraAnalysis.RIGHT_WHITE_SURFACE]
        green_color = [0.3, 1, 0.6, 1]
        if left_mesh is not None:
            left_mesh.set_color(green_color) 
            view.add_object(left_mesh)
        if right_mesh is not None:
            right_mesh.set_color(green_color)
            view.add_object(right_mesh)
        if left_mesh is not None or right_mesh is not None:
            mri = self._viewport_model.observed_objects[IntraAnalysis.CORRECTED_MRI]
            if mri is not None:
                view.add_object(mri)
