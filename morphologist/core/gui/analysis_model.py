import os
import hashlib
import threading
import time

from morphologist.core.gui.qt_backend import QtCore

class AnalysisPollingThread(QtCore.QThread):

    STOPPED = 0
    RUNNING = 1
    HELD = 2

    def __init__(self, observed_files):
        self.lock = threading.RLock()
        self._update_interval = 4 # in seconds
        self.state = self.STOPPED
        self.observed_files = observed_files

    def run(self):
        with self.lock:
            self.state = self.RUNNING
        while True:
            with self.lock:
                time.sleep(self._update_interval * 1000)
                state = int(self.state)
            if state == self.STOPPED:
                break
            elif state == RUNNING:
                self._check_output_files_changed()

    def _check_output_files_changed(self):
        pass


class LazyAnalysisModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    files_changed = QtCore.pyqtSignal(dict)

    def __init__(self, analysis=None, parent=None):
        super(LazyAnalysisModel, self).__init__(parent)
        self._analysis = None 
        self._output_parameters_file_sha = {}

        self._update_interval = 4 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        if analysis is not None:
            self.set_analysis(analysis)
        self._timer.timeout.connect(self._check_output_files_changed)

    def set_analysis(self, analysis):
        self._timer.stop()
        self._analysis = analysis
        self._output_parameters_file_sha = {} 
        self.changed.emit()
        self._emit_input_files_changed()
        self._timer.start()
        QtCore.QTimer.singleShot(100, self._timer.timeout.emit) 

    def remove_analysis(self):
        self._timer.stop()
        self._analysis = None
        self.changed.emit()

    def _emit_input_files_changed(self):
        self.files_changed.emit(
            self._analysis.list_input_parameters_with_existing_files())

    def _check_output_files_changed(self):
        #checked_outputs_names \
            #= self._analysis.get_output_file_parameter_names()
        #checked_outputs = dict([
            #(parameter_name,
             #getattr(self._analysis.pipeline.process, parameter_name))
            #for parameter_name in checked_outputs_names])
        checked_outputs = \
            self._analysis.list_output_parameters_with_existing_files()
        changed_parameters = self._changed_parameters(
            checked_outputs, self._output_parameters_file_sha)
        if len(changed_parameters) > 0:
            changed_parameters_with_details = {}
            for parameter_name in changed_parameters:
                changed_parameters_with_details[parameter_name] = \
                        getattr(self._analysis.pipeline.process,
                                parameter_name)
            self.files_changed.emit(changed_parameters_with_details)

    def _changed_parameters(self, existing_items, parameters_file_sha):
        changed_parameters = []
        for parameter_name, filename in existing_items.iteritems():
            if not os.path.exists(filename):
                # missing files are considered not changed
                # (which may be a problem if files are removed)
                continue
            # TODO: directories are ignored !
            if os.path.isdir(filename): continue
            last_sha = parameters_file_sha.get(parameter_name, None)
            new_sha = self._sha(filename)
            if new_sha != last_sha:
                parameters_file_sha[parameter_name] = new_sha
                changed_parameters.append(parameter_name)

        prev_parameters = set(parameters_file_sha.keys())
        new_parameters = set(existing_items.keys())
        deleted_parameters = prev_parameters.difference(new_parameters)
        for parameter_name in deleted_parameters:
            changed_parameters.append(parameter_name)
            del parameters_file_sha[parameter_name]

        return changed_parameters 

    def _sha(self, filename):
        with open(filename, "r") as fd:
            content = fd.read()
            sha = hashlib.sha1(content)
        return sha.hexdigest()
