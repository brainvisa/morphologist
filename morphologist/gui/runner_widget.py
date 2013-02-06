import os

from .qt_backend import QtCore, QtGui, loadUi 
from morphologist.gui import ui_directory 
from morphologist.runner import MissingInputFileError


class RunnerView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'runner_widget.ui')
    
    def __init__(self, parent=None):
        super(RunnerView, self).__init__(parent)
        self.ui = loadUi(self.uifile, self)
        self._runner_model = None
        self._disable_all_buttons()

    def _disable_all_buttons(self):
        self.ui.run_button.setEnabled(False)
        self.ui.stop_button.setEnabled(False)
        self.ui.erase_button.setEnabled(False)

    def set_model(self, model):
        if self._runner_model is not None:
            self._runner_model.runner_status_changed.disconnect(\
                                    self.on_runner_status_changed)
            self._runner_model.changed.disconnect(self.on_model_changed)
        self._runner_model = model
        self._runner_model.runner_status_changed.connect(\
                            self.on_runner_status_changed)
        self._runner_model.changed.connect(self.on_model_changed)

    @QtCore.Slot()
    def on_model_changed(self):
        study = self._runner_model.study
        if study.has_subjects():
            if not study.has_all_results():
                self.ui.run_button.setEnabled(True)
            if study.has_results():
                self.ui.erase_button.setEnabled(True)
        else:
            self.ui.run_button.setEnabled(False)
        
    @QtCore.Slot(bool)
    def on_runner_status_changed(self, running):
        if running:
            self._set_running_state()
        else:
            self._set_not_running_state()

    def _set_running_state(self):
        self.ui.run_button.setEnabled(False)
        self.ui.stop_button.setEnabled(True)
        self.ui.erase_button.setEnabled(False)

    def _set_not_running_state(self):
        self.ui.run_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)
        self._set_erase_button_if_needed()

    def _set_erase_button_if_needed(self):
        enable_erase_button = self._runner_model.study.has_results()
        self.ui.erase_button.setEnabled(enable_erase_button)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_run_button_clicked(self):
        '''calling assumption: a model must have been set with set_model.'''
        self.ui.run_button.setEnabled(False)
        if self._run_analyses():
            self.ui.stop_button.setEnabled(True)
        else:
            self.ui.run_button.setEnabled(True)

    def _run_analyses(self):
        run = False
        try:
            self._runner_model.runner.run()
            run = True
        except MissingInputFileError, e:
            QtGui.QMessageBox.critical(self, "Run analysis error", 
                        "Some input files do not exist.\n%s" %(e))
        return run
 
    # this slot is automagically connected
    @QtCore.Slot()
    def on_stop_button_clicked(self):
        '''calling assumption: a model must have been set with set_model.'''
        self.ui.stop_button.setEnabled(False)
        self._runner_model.runner.stop()
        self.ui.run_button.setEnabled(True)
        self._set_erase_button_if_needed()

    # this slot is automagically connected
    def on_erase_button_clicked(self):
        '''calling assumption: a model must have been set with set_model.'''
        self.ui.erase_button.setEnabled(False)
        self._runner_model.study.clear_results()
        self.ui.run_button.setEnabled(True)
