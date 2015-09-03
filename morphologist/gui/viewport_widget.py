import os

from morphologist.core.backends.mixins import ColorMap, ViewType
from morphologist.core.gui.object3d import Object3D, APCObject
from morphologist.core.gui.vector_graphics import Histogram, VectorExtendedView
from morphologist.core.backends import Backend
from morphologist.core.gui.viewport_widget import AnalysisViewportModel, \
                                    Object3DViewportView, VectorViewportView, \
                                    AnalysisViewportWidget, ViewportView
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames
from brainvisa.morphologist.qt4gui.histo_analysis_editor \
    import create_histo_editor
#from brainvisa.morphologist.qt4gui.histo_analysis_widget \
    #import load_histo_analysis

class IntraAnalysisViewportModel(AnalysisViewportModel):

    def __init__(self, model):
        super(IntraAnalysisViewportModel, self).__init__(model)

    def _init_3d_objects(self):
        self.observed_objects = { \
            IntraAnalysisParameterNames.MRI : None,
            IntraAnalysisParameterNames.COMMISSURE_COORDINATES : None, 
            IntraAnalysisParameterNames.CORRECTED_MRI : None,
            IntraAnalysisParameterNames.HISTO_ANALYSIS : None,
            IntraAnalysisParameterNames.BRAIN_MASK : None,
            IntraAnalysisParameterNames.SPLIT_MASK : None,
            IntraAnalysisParameterNames.LEFT_GREY_WHITE : None,
            IntraAnalysisParameterNames.RIGHT_GREY_WHITE : None,
            IntraAnalysisParameterNames.LEFT_GREY_SURFACE : None,
            IntraAnalysisParameterNames.RIGHT_GREY_SURFACE : None,
            IntraAnalysisParameterNames.LEFT_WHITE_SURFACE : None,
            IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE : None,
            IntraAnalysisParameterNames.LEFT_SULCI : None, 
            IntraAnalysisParameterNames.RIGHT_SULCI : None,
            IntraAnalysisParameterNames.LEFT_LABELED_SULCI : None, 
            IntraAnalysisParameterNames.RIGHT_LABELED_SULCI : None,
        }

    @staticmethod
    def load_object(parameter_name, filename):
        obj = None
        if (parameter_name == IntraAnalysisParameterNames.COMMISSURE_COORDINATES):
            obj = APCObject(filename)
        elif (parameter_name == IntraAnalysisParameterNames.HISTO_ANALYSIS):
            obj = Histogram.from_filename(filename)
        else:
            obj = Object3D.from_filename(filename) 
        return obj

    @staticmethod
    def load_object_async(parameter_name, filename, callback):
        _ = parameter_name
        obj = None
        if (parameter_name == IntraAnalysisParameterNames.COMMISSURE_COORDINATES):
            obj = APCObject(filename)
        elif (parameter_name == IntraAnalysisParameterNames.HISTO_ANALYSIS):
            obj = Histogram.from_filename(filename)
        else:
            Object3D.from_filename_async(filename, callback)
            return
        callback(obj)

    def _remove_useless_parameters(self, changed_parameters):
        for sulci, labelled_sulci in [(IntraAnalysisParameterNames.LEFT_SULCI,
                                       IntraAnalysisParameterNames.LEFT_LABELED_SULCI), 
                                      (IntraAnalysisParameterNames.RIGHT_SULCI,
                                       IntraAnalysisParameterNames.RIGHT_LABELED_SULCI)]:
            labeled_sulci_filename = changed_parameters.get(labelled_sulci, None)
            if (labeled_sulci_filename and os.path.exists(labeled_sulci_filename)):
                if changed_parameters.get(sulci, None):
                    changed_parameters.pop(sulci)


class IntraAnalysisViewportWidget(AnalysisViewportWidget):

    def _init_views(self, model):
        for view_class, line, column in [(RawMriACPCView, 0 ,0), 
                                         (BiasCorrectedMriView,0, 1), 
                                         (HistoAnalysisView,0, 2),
                                         (BrainMaskView,0, 3), 
                                         (SplitMaskView,1, 0), 
                                         (GreyWhiteView,1, 1), 
                                         (GreySurfaceView,1, 2), 
                                         (SulciView,1, 3)]:
            view = view_class(model)
            self._views.append(view)
            self._grid_layout.addWidget(view, line, column)


class RawMriACPCView(Object3DViewportView):
    
    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(RawMriACPCView, self).__init__(model, parent, view_type, 
                                             restricted_controls)
        self._observed_parameters = [IntraAnalysisParameterNames.MRI, 
                                     IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self.set_title(" 1 ) Raw MRI, AC/PC")
        self.set_tooltip("Raw T1 MRI + Anterior(blue)/Posterior(yellow) commissures")
        
    def update(self):
        self._view.clear()
        mri = self._viewport_model.observed_objects[IntraAnalysisParameterNames.MRI]
        if mri is not None:
            self._view.add_object(mri)
            self._view.center_on_object(mri)
        apc_object = self._viewport_model.observed_objects[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        if apc_object is not None:
            apc_object.set_ac_color(( 0, 0, 1, 1 )) 
            apc_object.set_pc_color(( 1, 1, 0, 1 )) 
            apc_object.set_ih_color(( 0, 1, 0, 1 ))
            self._view.add_object(apc_object)
            self._view.center_on_object(apc_object)


class BiasCorrectedMriView(Object3DViewportView):

    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(BiasCorrectedMriView, self).__init__(model, parent, view_type, 
                                                   restricted_controls)
        self._observed_parameters = [
            IntraAnalysisParameterNames.CORRECTED_MRI,
            IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self.set_title(" 2 ) Bias corrected MRI")

    def update(self):
        self._view.clear()
        corrected_mri = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.CORRECTED_MRI]
        if corrected_mri is not None:
            mri_copy = corrected_mri.shallow_copy()
            self._temp_object = mri_copy
            minv = None
            maxv = None
            histo = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.HISTO_ANALYSIS]
            if histo is not None:
                han = histo._friend_backend_object.han
                minv = max(0, han[0][0] - han[0][1] * 8)
                maxv = han[1][0] + han[1][1] * 3
            mri_copy.set_color_map(ColorMap.RAINBOW, minv, maxv)
            self._view.add_object(mri_copy)


class HistoAnalysisView(VectorViewportView):

    def __init__(self, model, parent=None):
        super(HistoAnalysisView, self).__init__(model, parent)
        self._observed_parameters = [
            IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self.set_title(" 3 ) Histogram")
        self.set_tooltip("""<p>Histogram analysis</p>
<p>Histogram curve in blue, it should contain two peaks: one (green analysis) for grey matter, one (red analysis) for white matter.</p>""")

    def create_extended_view(self):
        window = HistoAnalysisEditorView(self._viewport_model, self)
        from PyQt4 import QtCore
        window.setWindowFlags(QtCore.Qt.Window)
        window.ui.extend_view_button.setVisible(False)
        window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        window.update()
        return window

class HistoAnalysisEditorView(ViewportView):

    frame_style_sheet = ViewportView.frame_style_sheet + '''
        QPushButton {
            color: white;
            background-color: #606060;
        }
        QPushButton:hover {
            background-color: #808080;
        }
        QToolButton {
            color: white;
            background-color: black;
        }
        QToolButton:checked {
            color: white;
            background-color: #606060;
        }
        QToolButton:hover {
            color: white;
            background-color: #808080;
        }
        QToolBar {
            color: #808080;
            background: black;
        }
        QMenu {
            color: white;
            background-color: #606060;
        }
        QMenu::item:selected {
            color: white;
            background-color: #909090;
        }
        QMenuBar {
            color: white;
            background-color: #404040;
        }
        QMenuBar::item {
            border-radius: 2px;
            border-width: 2px;
            border-color: black;
            spacing: 3px;
            padding: 1px 4px;
            background: transparent;
        }
        QMenuBar::item:selected {
            background: #808080;
            border-radius: 2px;
            border-color: black;
        }
        QLineEdit {
            background-color: #909090;
        }
        QStatusBar {
            color: #a0a0a0;
        }
    '''

    def __init__(self, model, parent=None):
        super(HistoAnalysisEditorView, self).__init__(model, parent)
        self._view = VectorExtendedView(self.ui.view_hook)
        self._view.set_bgcolor(self.bg_color)
        self._observed_parameters = [
            IntraAnalysisParameterNames.HISTO_ANALYSIS,
            IntraAnalysisParameterNames.CORRECTED_MRI]
        self.set_title(" 3b ) Histogram edition")
        self.set_tooltip("""<p>Histogram analysis edition</p>
<p>Histogram curve in blue, it should contain two peaks: one (green analysis) for grey matter, one (red analysis) for white matter.</p>""")
        self.resize(800, 500)

    def _friend_visit(self, vector_graphic):
        self._backend.add_object_in_editor(vector_graphic._friend_backend_object, self._backend_view)

class BrainMaskView(Object3DViewportView):
    
    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(BrainMaskView, self).__init__(model, parent, view_type, 
                                            restricted_controls)
        self._observed_parameters = [IntraAnalysisParameterNames.BRAIN_MASK, 
                                     IntraAnalysisParameterNames.CORRECTED_MRI]
        self.set_title(" 4 ) Brain mask")

    def update(self):
        self._view.clear()
        mask = self._viewport_model.observed_objects[IntraAnalysisParameterNames.BRAIN_MASK]
        if mask is not None:
            mask.set_color_map(ColorMap.GREEN_MASK)
            mri = self._viewport_model.observed_objects[IntraAnalysisParameterNames.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(mri, mask, mode='linear', rate=0.7)
                self._temp_object = fusion
                self._view.add_object(fusion)
            else:
                self._view.add_object(mask) 


class SplitMaskView(Object3DViewportView):
    
    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(SplitMaskView, self).__init__(model, parent, view_type, 
                                            restricted_controls)
        self._observed_parameters = [IntraAnalysisParameterNames.SPLIT_MASK, 
                                     IntraAnalysisParameterNames.CORRECTED_MRI]
        self.set_title(" 5 ) Hemispheres mask")
        self.set_tooltip("Hemispheres and cerebellum mask")
    
    def update(self):
        self._view.clear()
        mask = self._viewport_model.observed_objects[IntraAnalysisParameterNames.SPLIT_MASK]
        if mask is not None:
            mask.set_color_map(ColorMap.RAINBOW_MASK)
            mri = self._viewport_model.observed_objects[IntraAnalysisParameterNames.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(mri, mask, mode='linear', rate=0.7)
                self._temp_object = fusion
                self._view.add_object(fusion)
            else:
                self._view.add_object(mask) 


class GreyWhiteView(Object3DViewportView):

    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(GreyWhiteView, self).__init__(model, parent, view_type, 
                                            restricted_controls)
        self._observed_parameters = [
            IntraAnalysisParameterNames.LEFT_GREY_WHITE,
            IntraAnalysisParameterNames.RIGHT_GREY_WHITE,
            IntraAnalysisParameterNames.CORRECTED_MRI]
        self.set_title(" 6 ) G/W classification")
        self.set_tooltip("Grey/White classification")

    def update(self):
        self._view.clear()
        left_mask = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        right_mask = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
        if left_mask is not None and right_mask is not None:
            left_mask.set_color_map(ColorMap.RAINBOW_MASK)
            right_mask.set_color_map(ColorMap.RAINBOW_MASK)
            mask_fusion = Object3D.from_fusion(
                left_mask, right_mask, mode='max_channel', rate=0.5)
            mri = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.CORRECTED_MRI]
            if mri is not None:
                fusion = Object3D.from_fusion(
                    mri, mask_fusion, mode='linear', rate=0.7)
                self._temp_object = fusion
                self._view.add_object(fusion)
            else:
                self._temp_object = mask_fusion
                self._view.add_object(mask_fusion)


class GreySurfaceView(Object3DViewportView):

    def __init__(self, model, parent=None, view_type=ViewType.THREE_D, 
                 restricted_controls=True):
        super(GreySurfaceView, self).__init__(model, parent, view_type, 
                                              restricted_controls)
        self._observed_parameters = [
            IntraAnalysisParameterNames.LEFT_GREY_SURFACE,
            IntraAnalysisParameterNames.RIGHT_GREY_SURFACE,
            IntraAnalysisParameterNames.CORRECTED_MRI]
        if view_type != ViewType.THREE_D:
            self._observed_parameters += [
                IntraAnalysisParameterNames.LEFT_WHITE_SURFACE,
                IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]
        self.set_title(" 7 ) Grey surface")

    def update(self):
        self._view.clear()
        left_mesh = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.LEFT_GREY_SURFACE]
        right_mesh = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.RIGHT_GREY_SURFACE]
        yellow_color = [0.9, 0.7, 0.0, 1]
        gw_color = [1., 0.7, 0.7, 1.]
        if left_mesh is not None or right_mesh is not None:
            mri = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.CORRECTED_MRI]
            if mri is not None:
                self._view.add_object(mri)
        if self.view_type() == ViewType.THREE_D:
            if left_mesh is not None:
                left_mesh.set_color(yellow_color)
                self._view.add_object(left_mesh)
            if right_mesh is not None:
                right_mesh.set_color(yellow_color)
                self._view.add_object(right_mesh)
        else: # 2D mode
            self._temp_object = []
            if left_mesh is not None:
                left_fus = Object3D.from_fusion(
                    left_mesh, method='Fusion2DMeshMethod')
                left_fus.set_color(yellow_color)
                self._temp_object = [left_fus]
                self._view.add_object(left_fus)
            if right_mesh is not None:
                right_fus = Object3D.from_fusion(
                    right_mesh, method='Fusion2DMeshMethod')
                right_fus.set_color(yellow_color)
                self._temp_object.append(right_fus)
                self._view.add_object(right_fus)
            left_gw_mesh = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]
            right_gw_mesh = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]
            if left_gw_mesh is not None:
                left_gw_fus = Object3D.from_fusion(
                    left_gw_mesh, method='Fusion2DMeshMethod')
                left_gw_fus.set_color(gw_color)
                self._temp_object.append(left_gw_fus)
                self._view.add_object(left_gw_fus)
            if right_gw_mesh is not None:
                right_gw_fus = Object3D.from_fusion(
                    right_gw_mesh, method='Fusion2DMeshMethod')
                right_gw_fus.set_color(gw_color)
                self._temp_object.append(right_gw_fus)
                self._view.add_object(right_gw_fus)


class SulciView(Object3DViewportView):

    def __init__(self, model, parent=None, view_type=ViewType.THREE_D, 
                 restricted_controls=True):
        super(SulciView, self).__init__(model, parent, view_type, 
                                        restricted_controls)
        if view_type == ViewType.THREE_D:
            self._observed_parameters \
                = [IntraAnalysisParameterNames.LEFT_WHITE_SURFACE,
                   IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE,
                   IntraAnalysisParameterNames.LEFT_SULCI,
                   IntraAnalysisParameterNames.RIGHT_SULCI,
                   IntraAnalysisParameterNames.LEFT_LABELED_SULCI,
                   IntraAnalysisParameterNames.RIGHT_LABELED_SULCI]
        else:
            self._observed_parameters \
                = [IntraAnalysisParameterNames.LEFT_SULCI,
                   IntraAnalysisParameterNames.RIGHT_SULCI,
                   IntraAnalysisParameterNames.LEFT_LABELED_SULCI,
                   IntraAnalysisParameterNames.RIGHT_LABELED_SULCI,
                   IntraAnalysisParameterNames.CORRECTED_MRI]
        self.set_title(" 8 ) White surface, Sulci")
        self.set_tooltip("Labeled sulci on white surface")

    def update(self):
        self._view.clear()
        left_mesh = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]
        right_mesh = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]
        left_sulci = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.LEFT_SULCI]
        right_sulci = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.RIGHT_SULCI]
        left_labeled_sulci = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.LEFT_LABELED_SULCI]
        right_labeled_sulci = self._viewport_model.observed_objects[
            IntraAnalysisParameterNames.RIGHT_LABELED_SULCI]
        grey_color = [0.8, 0.8, 0.8, 1.]
        if self.view_type() == ViewType.THREE_D and left_mesh is not None:
            left_mesh.set_color(grey_color) 
            self._view.add_object(left_mesh)
        if self.view_type() == ViewType.THREE_D and right_mesh is not None:
            right_mesh.set_color(grey_color)
            self._view.add_object(right_mesh)
        if left_labeled_sulci is not None:
            self._view.add_object(left_labeled_sulci)
        elif left_sulci is not None:
            self._view.add_object(left_sulci)
        if right_labeled_sulci is not None:
            self._view.add_object(right_labeled_sulci)
        elif right_sulci is not None:
            self._view.add_object(right_sulci)
        if ((left_mesh is not None) or (right_mesh is not None) or
            (left_sulci is not None) or (right_sulci is not None) or
            (left_labeled_sulci is not None) or
            (right_labeled_sulci is not None)) \
                and self.view_type() != ViewType.THREE_D:
            mri = self._viewport_model.observed_objects[
                IntraAnalysisParameterNames.CORRECTED_MRI]
            if mri is not None:
                self._view.add_object(mri)
        self._temp_object = []
        gw_color = [1., 0.7, 0.7, 1.]
        if self.view_type() != ViewType.THREE_D and left_mesh is not None:
            print 'add 2d mesh left'
            left_fus = Object3D.from_fusion(
                left_mesh, method='Fusion2DMeshMethod')
            left_fus.set_color(gw_color)
            print 'left_fus:', left_fus
            self._temp_object = [left_fus]
            self._view.add_object(left_fus)
        if self.view_type() != ViewType.THREE_D and right_mesh is not None:
            right_fus = Object3D.from_fusion(
                right_mesh, method='Fusion2DMeshMethod')
            right_fus.set_color(gw_color)
            self._temp_object.append(right_fus)
            self._view.add_object(right_fus)
