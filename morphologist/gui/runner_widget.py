import os

from .qt_backend import QtCore, QtGui, loadUi 
from morphologist.gui import ui_directory 
from morphologist.runner import OutputFileExistError, MissingInputFileError


class RunnerView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'runner_widget.ui')
    
    def __init__(self, parent=None):
        super(RunnerView, self).__init__(parent)
        self.ui = loadUi(self.uifile, self)
        self._runner_model = None

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
        if self._runner_model.study.has_subjects():
            self.ui.run_button.setEnabled(True)
        else:
            self.ui.run_button.setEnabled(False)
        
    @QtCore.Slot(bool)
    def on_runner_status_changed(self, running):
        if running:
            self.ui.run_button.setEnabled(False)
            self.ui.stop_button.setEnabled(True)
        else:
            self.ui.run_button.setEnabled(True)
            self.ui.stop_button.setEnabled(False)
              
    # this slot is automagically connected
    @QtCore.Slot()
    def on_run_button_clicked(self):
        if self._runner_model is not None:
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
            QtGui.QMessageBox.critical(self, 
                                       "Run analysis error", 
                                       "Some input files do not exist.\n%s" %(e))
        except OutputFileExistError, e:
            answer = QtGui.QMessageBox.question(self, "Existing results",
                                                "Some results already exist.\n" 
                                                "Do you want to delete them ?", 
                                                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if answer == QtGui.QMessageBox.Yes:
                self._runner_model.study.clear_results()
                run = self._run_analyses()
        return run
 
    # this slot is automagically connected
    @QtCore.Slot()
    def on_stop_button_clicked(self):
        if self._runner_model is not None:
            self.ui.stop_button.setEnabled(False)
            self._runner_model.runner.stop()
            self.ui.run_button.setEnabled(True)
