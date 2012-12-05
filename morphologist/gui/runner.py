import os

from .qt_backend import QtCore, QtGui, loadUi 
from .gui import ui_directory 
from morphologist.analysis import MissingParameterValueError
from morphologist.runner import OutputFileExistError, MissingInputFileError


class RunnerView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'runner.ui')
    
    def __init__(self, parent=None):
        super(RunnerView, self).__init__(parent)
        self.ui = loadUi(self.uifile, self)
        self._model = None

        
    def set_model(self, model):
        if self._model is not None:
            self._model.runner_status_changed.disconnect(self.on_model_changed)
        self._model = model
        self._model.runner_status_changed.connect(self.on_model_changed)
    
    @QtCore.Slot(bool)
    def on_model_changed(self, running):
        if running:
            self.ui.run_button.setEnabled(False)
            self.ui.stop_button.setEnabled(True)
        else:
            self.ui.run_button.setEnabled(True)
            self.ui.stop_button.setEnabled(False)
   
    def _run_analyses(self):
        run = False
        try:
            self._model.runner.run()
            run = True
        except MissingParameterValueError, e:
            QtGui.QMessageBox.critical(self, 
                                       "Run analysis error", 
                                       "Some parameter value are missing.\n%s" %(e))
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
                self._model.study.clear_results()
                run = self._run_analyses()
        return run
            
    @QtCore.Slot()
    def on_run_button_clicked(self):
        if self._model is not None:
            self.ui.run_button.setEnabled(False)
            if self._run_analyses():
                self.ui.stop_button.setEnabled(True)
            else:
                self.ui.run_button.setEnabled(True)

    @QtCore.Slot()
    def on_stop_button_clicked(self):
        if self._model is not None:
            self.ui.stop_button.setEnabled(False)
            self._model.runner.stop()
            self.ui.run_button.setEnabled(True)
            