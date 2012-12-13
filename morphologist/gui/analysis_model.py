import os

from .qt_backend import QtCore, QtGui, loadUi 


class LazyAnalysisModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    input_files_changed = QtCore.pyqtSignal(list)
    output_files_changed = QtCore.pyqtSignal(list)

    def __init__(self, analysis=None, parent=None):
        super(LazyAnalysisModel, self).__init__(parent)
        self._analysis = None 
        self._input_parameters_file_modification_time = {}
        self._output_parameters_file_modification_time = {}

        self._update_interval = 2 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        if analysis is not None:
            self.set_analysis(analysis)
        self._timer.start()

    def set_analysis(self, analysis):
        if self._analysis is None:
            self._analysis = analysis 
            self._timer.timeout.connect(self._check_output_files_changed)
        else:
            self._analysis = analysis 
        self._input_parameters_file_modification_time = {}
        self._output_parameters_file_modification_time = {}
        self.changed.emit()
        self._check_input_files_changed()

    def remove_analysis(self):
        if self._analysis is not None:
            self._timer.timeout.disconnect(self._check_output_files_changed)
        self._analysis = None
        self.changed.emit()
              
    def _check_input_files_changed(self):
        checked_inputs = \
            self._analysis.input_params.list_parameters_with_existing_files()
        changed_input_parameters = self._changed_parameters(checked_inputs,
                            self._input_parameters_file_modification_time)
        if len(changed_input_parameters) > 0:
            self.input_files_changed.emit(changed_input_parameters)

    def _check_output_files_changed(self):
        checked_outputs = \
            self._analysis.output_params.list_parameters_with_existing_files()
        changed_output_parameters = self._changed_parameters(checked_outputs,
                            self._output_parameters_file_modification_time)
        if len(changed_output_parameters) > 0:
            self.output_files_changed.emit(changed_output_parameters)

    def _changed_parameters(self, existing_items,
            parameters_file_modification_time):
        changed_parameters = []
        for parameter_name, filename in existing_items.items():
            stat = os.stat(filename)
            last_modification_time = parameters_file_modification_time.get(parameter_name, 0)
            new_modification_time = stat.st_mtime
            if new_modification_time > last_modification_time:
                parameters_file_modification_time[parameter_name] = \
                                                    new_modification_time
                changed_parameters.append(parameter_name)

        prev_parameters = set(parameters_file_modification_time.keys())
        new_parameters = set(existing_items.keys())
        deleted_parameters = prev_parameters.difference(new_parameters)
        for parameter_name in deleted_parameters:
            changed_parameters.append(parameter_name)
            del parameters_file_modification_time[parameter_name]
        
        return changed_parameters

    def filename_from_input_parameter(self, parameter):
        return self._analysis.input_params[parameter]

    def filename_from_output_parameter(self, parameter):
        return self._analysis.output_params[parameter]
