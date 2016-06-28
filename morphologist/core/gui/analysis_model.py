import os
import hashlib
import threading
import time
import six

from morphologist.core.gui.qt_backend import QtCore

class AnalysisPollingThread(QtCore.QThread):

    files_changed = QtCore.pyqtSignal(dict)
    STOPPED = 0
    RUNNING = 1
    HELD = 2
    ASK_CHECK = 3

    def __init__(self, analysis, parent=None):
        super(AnalysisPollingThread, self).__init__(parent)
        self.lock = threading.RLock()
        self._update_interval = 4 # in seconds
        self._update_sub_interval = 0.2
        self.state = self.STOPPED
        self.set_analysis(analysis)

    def set_analysis(self, analysis):
        with self.lock:
            self._analysis = analysis
            self._output_parameters_file_sha = {}
            self.observed_files = self._get_observed_files()

    def run(self):
        with self.lock:
            self.state = self.RUNNING
        running = True
        while running:
                with self.lock:
                    state = int(self.state)
                if state == self.STOPPED:
                    running = False
                    break
                elif state == self.RUNNING:
                    self._check_output_files_changed()
                for i in range(int(
                        self._update_interval / self._update_sub_interval)):
                    time.sleep(self._update_sub_interval)
                    with self.lock:
                        state = int(self.state)
                    if state == self.STOPPED:
                        running = False
                        break
                    elif state == self.ASK_CHECK:
                        with self.lock:
                            self.state = self.RUNNING
                        break  # restart loop

    def _get_observed_files(self):
        if self._analysis is None:
            return {}
        checked_outputs_names \
            = self._analysis.get_output_file_parameter_names()
        self._analysis.propagate_parameters()
        checked_outputs = dict([
            (parameter_name,
             getattr(self._analysis.pipeline, parameter_name))
            for parameter_name in checked_outputs_names])
        return checked_outputs

    def _check_output_files_changed(self):
        with self.lock:
            checked_outputs = dict(self.observed_files)
        changed_parameters = self._changed_parameters(
            checked_outputs, self._output_parameters_file_sha)
        if len(changed_parameters) > 0:
            changed_parameters_with_details = {}
            for parameter_name in changed_parameters:
                changed_parameters_with_details[parameter_name] = \
                        checked_outputs[parameter_name]
            self.files_changed.emit(changed_parameters_with_details)

    def _changed_parameters(self, existing_items, parameters_file_sha):
        changed_parameters = []
        for parameter_name, filename in six.iteritems(existing_items):
            if filename is None:
                continue
            import traits.api as traits
            if filename is traits.Undefined:
                print('undefined filename for param:', parameter_name)
            # TODO: directories are ignored !
            if os.path.isdir(filename): continue
            if not os.path.exists(filename):
                if parameters_file_sha.has_key(parameter_name):
                    del parameters_file_sha[parameter_name]
                    changed_parameters.append(parameter_name)
                continue
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


class LazyAnalysisModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    files_changed = QtCore.pyqtSignal(dict)

    def __init__(self, analysis=None, parent=None):
        super(LazyAnalysisModel, self).__init__(parent)
        self._analysis = None
        self.polling_thread = None

        if analysis is not None:
            self.set_analysis(analysis)

    def __del__(self):
        if self.polling_thread is not None:
            with self.polling_thread.lock:
                self.polling_thread.state = AnalysisPollingThread.STOPPED
            self.polling_thread.terminate()
            self.polling_thread.wait()
            del self.polling_thread

    def set_analysis(self, analysis):
        if analysis is None:
            self.remove_analysis()
            return
        self._analysis = analysis
        self.changed.emit()
        self._emit_input_files_changed()

        if self.polling_thread is None:
            self.polling_thread = AnalysisPollingThread(self._analysis,
                                                        self)
            self.polling_thread.files_changed.connect(self.files_changed)
            self.polling_thread.start()
        else:
            restart = False
            with self.polling_thread.lock:
                if self.polling_thread.state == AnalysisPollingThread.STOPPED:
                    restart = True
                self.polling_thread.state = AnalysisPollingThread.HELD
            self.polling_thread.set_analysis(self._analysis)
            if restart:
                self.polling_thread.start()
            else:
                with self.polling_thread.lock:
                    self.polling_thread.state = AnalysisPollingThread.ASK_CHECK

    def remove_analysis(self):
        self._analysis = None

        if self.polling_thread is not None:
            with self.polling_thread.lock:
                self.polling_thread.state = AnalysisPollingThread.STOPPED
            self.polling_thread.set_analysis(None)

        self.changed.emit()

    def _emit_input_files_changed(self):
        self.files_changed.emit(
            self._analysis.list_input_parameters_with_existing_files())

