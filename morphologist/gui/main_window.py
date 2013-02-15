import os

from morphologist.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.gui import ui_directory 
from morphologist.intra_analysis_study import IntraAnalysisStudy
from morphologist.study import StudySerializationError
from morphologist.gui.study_editor_widget import StudyEditorDialog
from morphologist.runner import SomaWorkflowRunner
from morphologist.gui.study_model import LazyStudyModel
from morphologist.gui.analysis_model import LazyAnalysisModel
from morphologist.gui.viewport_widget import IntraAnalysisViewportModel,\
                             IntraAnalysisViewportView
from morphologist.gui.subjects_widget import SubjectsTableModel, SubjectsTableView
from morphologist.gui.runner_widget import RunnerView
from morphologist.analysis import ImportationError


class IntraAnalysisWindow(QtGui.QMainWindow):
    uifile = os.path.join(ui_directory, 'main_window.ui')

    def __init__(self, study_file=None, enable_brainomics_db=False):
        super(IntraAnalysisWindow, self).__init__()
        self.ui = loadUi(self.uifile, self)

        self.study = None
        self.runner = None
        self.study_model = LazyStudyModel()
        self.analysis_model = LazyAnalysisModel()
        self.study_tablemodel = SubjectsTableModel(self.study_model)
        self.study_selection_model = QtGui.QItemSelectionModel(self.study_tablemodel)
 
        self.study_view = SubjectsTableView()
        self.study_view.set_model(self.study_tablemodel)
        self.study_view.set_selection_model(self.study_selection_model)
        self.ui.study_widget_dock.setWidget(self.study_view)
        
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)

        self.viewport_model = IntraAnalysisViewportModel(self.analysis_model)
        self.viewport_view = IntraAnalysisViewportView(self.viewport_model, 
                                                       self.ui.viewport_frame)

        self.runner_view = RunnerView()
        self.runner_view.set_model(self.study_model)
        self.ui.runner_widget_dock.setWidget(self.runner_view)
        
        self.study_editor_widget_window = None
        self.enable_brainomics_db = enable_brainomics_db

        self._init_qt_connections()

        self.set_study(self._create_study(study_file))

    def _init_qt_connections(self):
        self.study_selection_model.currentChanged.connect(self.on_selection_changed)

    def _create_study(self, study_file=None):
        if study_file:
            study = IntraAnalysisStudy.from_file(study_file)
            return study
        else:
            return IntraAnalysisStudy()
        
    def _create_runner(self, study):
        return SomaWorkflowRunner(study)

    @QtCore.Slot()
    def on_action_new_study_triggered(self):
        msg = 'Stop current running analysis and create a new study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        study = self._create_study()
        self.study_editor_widget_window = StudyEditorDialog(study, parent=self,
                                            enable_brainomics_db=self.enable_brainomics_db)
        self.study_editor_widget_window.ui.accepted.connect(self.on_study_dialog_accepted)
        self.study_editor_widget_window.ui.show()
        
    @QtCore.Slot()
    def on_study_dialog_accepted(self):
        study = self.study_editor_widget_window.study
        parameter_template = self.study_editor_widget_window.parameter_template
        if study.has_subjects():
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            try:
                study.import_data(parameter_template)
            except ImportationError, e:
                QtGui.QApplication.restoreOverrideCursor()
                QtGui.QMessageBox.critical(self, 
                                          "Cannot import some images", "%s" %(e)) 
            else:
                QtGui.QApplication.restoreOverrideCursor()
            if study.has_subjects():
                msg = "The images have been imported in %s directory." % study.outputdir
                msgbox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                   "Images importation", msg,
                                   QtGui.QMessageBox.Ok, self)
                msgbox.show()
                
            study.set_analysis_parameters(parameter_template)
        self.set_study(study)
        self._try_save_to_backup_file()
        self.study_editor_widget_window = None

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_open_study_triggered(self):
        msg = 'Stop current running analysis and open a study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        backup_filename = QtGui.QFileDialog.getOpenFileName(self.ui,
                                caption="Open a study", directory="", 
                                options=QtGui.QFileDialog.DontUseNativeDialog)
        if backup_filename:
            try:
                study = self._create_study(backup_filename)
            except StudySerializationError, e:
                QtGui.QMessageBox.critical(self, 
                                          "Cannot load the study", "%s" %(e))
            else:
                self.set_study(study) 

    def _runner_still_running_after_stopping_asked_to_user(self,
                        msg='Stop current running analysis ?'):
        if self.runner.is_running():
            title = 'Analyses are currently running'
            answer = QtGui.QMessageBox.question(self, title, msg,
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.Cancel)
            if answer == QtGui.QMessageBox.Yes:
                self.runner.stop()
                return False
            else:
                return True
        return False

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_save_study_triggered(self):
        self._try_save_to_backup_file()

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_save_as_study_triggered(self):
        backup_filename = QtGui.QFileDialog.getSaveFileName(self.ui,
                                caption="Save a study", directory="", 
                                options=QtGui.QFileDialog.DontUseNativeDialog)
        if backup_filename:
            self.study.backup_filename = backup_filename
            self._try_save_to_backup_file()

    def _try_save_to_backup_file(self):
        try:
            self.study.save_to_backup_file()
        except StudySerializationError, e:
            QtGui.QMessageBox.critical(self, "Cannot save the study", "%s" %(e))

    @QtCore.Slot("const QModelIndex &", "const QModelIndex &")
    def on_selection_changed(self, current, previous):
        subject = self.study_tablemodel.subject_from_row_index(current.row())
        analysis = self.study.analyses[subject.id()]
        self.analysis_model.set_analysis(analysis)

    def set_study(self, study):
        self.study = study
        self.runner = self._create_runner(self.study)
        self.study_model.set_study_and_runner(self.study, self.runner)
        if not self.study.has_subjects():
            self.analysis_model.remove_analysis()
        self.setWindowTitle(self._window_title())

    def _window_title(self):
        return "Morphologist - %s" % self.study.name
    
    def closeEvent(self, event):
        msg = 'Stop current running analysis and quit ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): 
            event.ignore()
        else:
            event.accept()


def create_main_window(study_file=None, mock=False, enable_brainomics_db=False):
    if not mock:
        return IntraAnalysisWindow(study_file, enable_brainomics_db)
    else:
        from morphologist.tests.intra_analysis.mocks.main_window import MockIntraAnalysisWindow
        return MockIntraAnalysisWindow(study_file, enable_brainomics_db) 
