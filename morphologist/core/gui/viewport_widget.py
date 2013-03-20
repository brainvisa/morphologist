import os

from morphologist.core.backends.mixins import LoadObjectError
from morphologist.core.gui.object3d import Object3D
from morphologist.core.gui.qt_backend import QtCore 


class AnalysisViewportModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    parameter_changed = QtCore.pyqtSignal(list)

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
        self.observed_objects = {}
        raise NotImplementedError("SubjectwiseViewportModel is an abstract class")

    @QtCore.Slot()
    def on_analysis_model_changed(self):
        # XXX : may need a cache ?
        self._init_3d_objects()
        self.changed.emit()

    @QtCore.Slot(dict)
    def on_analysis_model_files_changed(self, changed_parameters):
        updated_parameters = []
        self._remove_useless_parameters(changed_parameters)
        for parameter_name, filename in changed_parameters.iteritems():
            if parameter_name in self.observed_objects.keys():
                self._update_observed_objects(parameter_name, filename)
                updated_parameters.append(parameter_name)
        self.parameter_changed.emit(updated_parameters)
        
    def _update_observed_objects(self, parameter_name, filename):
        object3d = self.observed_objects[parameter_name]
        if object3d is not None:
            if os.path.exists(filename):
                object3d.reload()
            else:
                object3d = None
        else:
            try:
                object3d = self.load_object(parameter_name, filename)
            except LoadObjectError:
                object3d = None
        self.observed_objects[parameter_name] = object3d

    @staticmethod
    def load_object(parameter_name, filename):
        _ = parameter_name
        return Object3D.from_filename(filename)
    
    def _remove_useless_parameters(self, changed_parameters):
        pass

