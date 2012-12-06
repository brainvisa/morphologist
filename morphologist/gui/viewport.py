import os

from morphologist.backends import Backend
from .qt_backend import QtCore, QtGui, loadUi 
from .gui import ui_directory 


class LazyAnalysisModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    input_parameters_changed = QtCore.pyqtSignal(list)
    output_parameters_changed = QtCore.pyqtSignal(list)

    def __init__(self, analysis=None, parent=None):
        super(LazyAnalysisModel, self).__init__(parent)
        self._analysis = None 
        self._modification_time_of_existing_files = {}

        self._update_interval = 2 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        if analysis is not None:
            self.set_analysis(analysis)
        self._timer.start()

    def set_analysis(self, analysis):
        if self._analysis is None:
            self._analysis = analysis 
            self._timer.timeout.connect(self._check_output_changed_files)
        else:
            self._analysis = analysis 
        self._modification_time_of_existing_files = {}
        self.changed.emit()
        self._check_input_changed_files()

    def _check_input_changed_files(self):
        checked_inputs = \
            self._analysis.input_params.list_parameters_with_existing_files()
        changed_input_parameters = self._changed_parameters(checked_inputs)
        self.input_parameters_changed.emit(changed_input_parameters)

    def _check_output_changed_files(self):
        checked_outputs = \
            self._analysis.output_params.list_parameters_with_existing_files()
        changed_output_parameters = self._changed_parameters(checked_outputs)
        self.output_parameters_changed.emit(changed_output_parameters)

    def _changed_parameters(self, checked_items):
        changed_parameters = []
        for parameter_name, filename in checked_items.items():
            stat = os.stat(filename)
            last_modification_time = self._modification_time_of_existing_files.get(filename, 0)
            new_modification_time = stat.st_mtime
            if new_modification_time > last_modification_time:
                self._modification_time_of_existing_files[filename] = new_modification_time
                changed_parameters.append(parameter_name)
        return changed_parameters

    def filename_from_input_parameter(self, parameter):
        return self._analysis.input_params[parameter]

    def filename_from_output_parameter(self, parameter):
        return self._analysis.output_params[parameter]


class SubjectwiseViewportModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()

    def __init__(self):
        super(SubjectwiseViewportModel, self).__init__()
        self._analysis_model = None

    def setModel(self, model):
        if self._analysis_model is not None:
            self._analysis_model.changed.disconnect(\
                        self.on_analysis_model_changed)
            self._analysis_model.input_parameters_changed.disconnect(\
                        self.on_analysis_model_input_parameters_changed)
            self._analysis_model.output_parameters_changed.disconnect(\
                        self.on_analysis_model_output_parameters_changed)
        self._analysis_model = model
        self._analysis_model.changed.connect(self.on_analysis_model_changed)
        self._analysis_model.input_parameters_changed.connect(\
                self.on_analysis_model_input_parameters_changed)
        self._analysis_model.output_parameters_changed.connect(\
                self.on_analysis_model_output_parameters_changed)
        self.changed.emit()

    @QtCore.Slot()
    def on_analysis_model_changed(self):
        raise Exception("SubjectwiseViewportModel is an abstract class")

    @QtCore.Slot(list)
    def on_analysis_model_input_parameters_changed(self, changed_parameters):
        raise Exception("SubjectwiseViewportModel is an abstract class")

    @QtCore.Slot(list)
    def on_analysis_model_output_parameters_changed(self, changed_parameters):
        raise Exception("SubjectwiseViewportModel is an abstract class")


class IntraAnalysisSubjectwiseViewportModel(SubjectwiseViewportModel):
    changed = QtCore.pyqtSignal()
    raw_mri_changed = QtCore.pyqtSignal()
    corrected_mri_changed = QtCore.pyqtSignal()
    brain_mask_changed = QtCore.pyqtSignal()
    split_mask_changed = QtCore.pyqtSignal()
    signal_map = { \
        'mri' : 'raw_mri_changed',
        'mri_corrected' : 'corrected_mri_changed',
        'brain_mask' : 'brain_mask_changed',
        'split_mask' : 'split_mask_changed'
    }

    def __init__(self):
        super(IntraAnalysisSubjectwiseViewportModel, self).__init__()
        self._objects_loader_backend = Backend.objects_loader_backend()
        self.__init__3d_objects()

    def __init__3d_objects(self):
        self.observed_objects = { \
            'mri' : None,
            'mri_corrected' : None,
            'brain_mask' : None,
            'split_mask' : None
        }

    @QtCore.Slot()
    def on_analysis_model_changed(self):
        # XXX : may need a cache ?
        self.__init__3d_objects()
        self.changed.emit()

    @QtCore.Slot(list)
    def on_analysis_model_input_parameters_changed(self, changed_inputs):
        self._on_analysis_model_parameters_changed(changed_inputs,
                self._analysis_model.filename_from_input_parameter)

    @QtCore.Slot(list)
    def on_analysis_model_output_parameters_changed(self, changed_outputs):
        self._on_analysis_model_parameters_changed(changed_outputs,
                self._analysis_model.filename_from_output_parameter)

    def _on_analysis_model_parameters_changed(self, changed_parameters,
                                                filename_from_parameter):
        for parameter in changed_parameters:
            if not parameter in self.observed_objects.keys():
                continue
            object = self.observed_objects[parameter]
            if object is not None:
                self._objects_loader_backend.delete_objects([object])
            filename = filename_from_parameter(parameter)
            try:
                object = self._objects_loader_backend.load_object(filename)
            except Exception, e:
                # XXX: should be propagated to the GUI ?
                print "error: parameter '%s':" % parameter, \
                        "can't load '%s'" % filename, e 
                continue
            self.observed_objects[parameter] = object
            signal = self.signal_map.get(parameter)
            if signal is not None:
                self.__getattribute__(signal).emit()
            

class IntraAnalysisSubjectwiseViewportView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'viewport.ui')
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
        super(IntraAnalysisSubjectwiseViewportView, self).__init__(parent)
        self.ui = loadUi(self.uifile, parent)
        self._view_hooks = [self.ui.view1_hook, self.ui.view2_hook, 
                            self.ui.view3_hook, self.ui.view4_hook]
        self._views = []
        self._objects_view1 = []
        self._objects_view2 = []
        self._objects_view3 = []
        self._objects_view4 = []
        self._display_lib = IntraAnalysisDisplayLibrary()
        self._model = None

        self._init_widget()

    def setModel(self, model):
        if self._model is not None:
            self._model.changed.disconnect(self.on_model_changed)
            self._model.raw_mri_changed.disconnect(self.on_raw_mri_changed)
            self._model.corrected_mri_changed.disconnect(\
                            self.on_corrected_mri_changed)
            self._model.brain_mask_changed.disconnect(\
                            self.on_brain_mask_changed)
            self._model.split_mask_changed.disconnect(\
                            self.on_split_mask_changed)
        self._model = model
        self._model.changed.connect(self.on_model_changed)
        self._model.raw_mri_changed.connect(self.on_raw_mri_changed)
        self._model.corrected_mri_changed.connect(self.on_corrected_mri_changed)
        self._model.brain_mask_changed.connect(self.on_brain_mask_changed)
        self._model.split_mask_changed.connect(self.on_split_mask_changed)

    def _init_widget(self):
        self.ui.setStyleSheet(self.main_frame_style_sheet)
        for view_hook in self._view_hooks:
            layout = QtGui.QVBoxLayout(view_hook)
        self._create_intra_analysis_views()

    def _create_intra_analysis_views(self):
        self.view1 = self._display_lib.create_normalized_raw_T1_with_ACPC_view(self.ui.view1_hook)

        self.view2 = self._display_lib.create_bias_corrected_T1_view(self.ui.view2_hook)
        self.view3 = self._display_lib.create_brain_mask_view(self.ui.view3_hook)
        self.view4 = self._display_lib.create_split_brain_view(self.ui.view4_hook)
        self._views = [self.view1, self.view2, self.view3, self.view4]
        self._display_lib.initialize_views(self._views)
        
    @QtCore.Slot()
    def on_model_changed(self):
        self._display_lib._backend.remove_objects_from_window(self._objects_view1, self.view1)
        self._display_lib._backend.remove_objects_from_window(self._objects_view2, self.view2)
        self._display_lib._backend.remove_objects_from_window(self._objects_view3, self.view3)
        self._display_lib._backend.remove_objects_from_window(self._objects_view4, self.view4)
        self._objects_view1 = []
        self._objects_view2 = []
        self._objects_view3 = []
        self._objects_view4 = []

        
    @QtCore.Slot()
    def on_raw_mri_changed(self):
        object = self._model.observed_objects['mri']
        self._objects_view1.append(object)
        self._display_lib._backend.add_objects_to_window(object, self.view1)
        self._display_lib._backend.center_window_on_object(self.view1, object)

    @QtCore.Slot()
    def on_corrected_mri_changed(self):
        object = self._model.observed_objects['mri_corrected']
        self._objects_view2.append(object)
        self._display_lib._backend.add_objects_to_window(object, self.view2)

    @QtCore.Slot()
    def on_brain_mask_changed(self):
        object = self._model.observed_objects['brain_mask']
        self._objects_view3.append(object)
        self._display_lib._backend.add_objects_to_window(object, self.view3)

    @QtCore.Slot()
    def on_split_mask_changed(self):
        object = self._model.observed_objects['split_mask']
        self._objects_view4.append(object)
        self._display_lib._backend.add_objects_to_window(object, self.view4)


class DisplayLibrary(object):
    
    def __init__(self, backend):
        self._backend = backend
        self._backend.initialize_display()


class IntraAnalysisDisplayLibrary(DisplayLibrary):

    def __init__(self, backend=Backend.display_backend()):
        super(IntraAnalysisDisplayLibrary, self).__init__(backend)

    def create_normalized_raw_T1_with_ACPC_view(self, parent=None):
        return self._backend.create_axial_view(parent)

    def create_bias_corrected_T1_view(self, parent=None):
        return self._backend.create_axial_view(parent)

    def create_brain_mask_view(self, parent=None):
        return self._backend.create_axial_view(parent)

    def create_split_brain_view(self, parent=None):
        return self._backend.create_axial_view(parent)

    def initialize_views(self, views):
        self._backend.set_bgcolor_views(views, [0., 0., 0., 1.])
     
