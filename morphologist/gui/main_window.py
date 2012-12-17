import os

from .qt_backend import QtCore, QtGui, loadUi 
from morphologist.gui import ui_directory 
from morphologist.study import Study
from morphologist.study import StudySerializationError
from .study_editor_widget import StudyEditorDialog
from morphologist.intra_analysis import IntraAnalysis
from morphologist.runner import SomaWorkflowRunner
from .study_model import LazyStudyModel
from morphologist.gui.analysis_model import LazyAnalysisModel
from .viewport_widget import IntraAnalysisViewportModel,\
                             IntraAnalysisViewportView
from .subjects_widget import SubjectsTableModel, SubjectsTableView
from .runner_widget import RunnerView


class IntraAnalysisWindow(QtGui.QMainWindow):
    uifile = os.path.join(ui_directory, 'main_window.ui')

    def __init__(self, study_file=None):
        super(IntraAnalysisWindow, self).__init__()
        self.ui = loadUi(self.uifile, self)

        self.study = None
        self.runner = None
        self.study_model = LazyStudyModel()
        self.analysis_model = LazyAnalysisModel()
        self.study_tablemodel = SubjectsTableModel(self.study_model)
        self.study_selection_model = QtGui.QItemSelectionModel(\
                                            self.study_tablemodel)
        self.viewport_model = IntraAnalysisViewportModel(
                                                    self.analysis_model)

        self.study_view = SubjectsTableView(self.ui.study_widget_dock)
        self.study_view.set_model(self.study_tablemodel)
        self.study_view.set_selection_model(self.study_selection_model)
        self.ui.study_widget_dock.setWidget(self.study_view)

        self.viewport_view = IntraAnalysisViewportView(\
                                        self.ui.viewport_frame)
        self.viewport_view.set_model(self.viewport_model)

        self.runner_view = RunnerView(self.ui.runner_frame)
        layout = QtGui.QVBoxLayout()
        self.ui.runner_frame.setLayout(layout)
        layout.addWidget(self.runner_view)
        self.runner_view.set_model(self.study_model)
        
        self.study_editor_widget_window = None

        self._init_qt_connections()
        self._init_widget()

        self.set_study(self._create_study(study_file))

    def _init_qt_connections(self):
        self.study_selection_model.currentChanged.connect(self.on_selection_changed)

    def _init_widget(self):
        pass

    def _create_study(self, study_file=None):
        if study_file:
            study = Study.from_file(study_file)
            return study
        else:
            return Study()
        
    def _create_runner(self, study):
        return SomaWorkflowRunner(study)

    @QtCore.Slot()
    def on_action_new_study_triggered(self):
        study = self._create_study()
        self.study_editor_widget_window = StudyEditorDialog(study, self)
        self.study_editor_widget_window.ui.accepted.connect(self.on_study_dialog_accepted)
        self.study_editor_widget_window.ui.show()
        
    @QtCore.Slot()
    def on_study_dialog_accepted(self):
        study = self.study_editor_widget_window.study
        if study.has_subjects():
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            study.import_data(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)
            study.set_analysis_parameters(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)
            QtGui.QApplication.restoreOverrideCursor()
            msg = "The images have been copied in %s directory." % study.outputdir
            msgbox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                   "Images importation", msg,
                                   QtGui.QMessageBox.Ok, self)
            msgbox.show()
        self.set_study(study)
        self.study_editor_widget_window = None


    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_open_study_triggered(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.ui, caption = "Open a study", directory="", 
                                                     options=QtGui.QFileDialog.DontUseNativeDialog)
        if filename:
            try:
                study = self._create_study(filename)
            except StudySerializationError, e:
                QtGui.QMessageBox.critical(self, 
                                          "Cannot load the study", "%s" %(e))
            else:
                self.set_study(study) 

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_save_study_triggered(self):
        filename = QtGui.QFileDialog.getSaveFileName(self.ui, caption="Save a study", directory="", 
                                                     options=QtGui.QFileDialog.DontUseNativeDialog)
        if filename:
            try:
                self.study.save_to_file(filename)
            except StudySerializationError, e:
                QtGui.QMessageBox.critical(self, 
                                          "Cannot save the study", "%s" %(e))

    # FIXME : move code elsewhere
    @QtCore.Slot("const QModelIndex &", "const QModelIndex &")
    def on_selection_changed(self, current, previous):
        subjectname = self.study_tablemodel.subjectname_from_row_index(current.row())
        analysis = self.study.analyses[subjectname]
        self.analysis_model.set_analysis(analysis)

    def set_study(self, study):
        self.study = study
        self.runner = self._create_runner(self.study)
        self.study_model.set_study_and_runner(self.study, self.runner)
        if not self.study.has_subjects():
            self.analysis_model.remove_analysis()
        self.setWindowTitle("Morphologist - %s" % self.study.name)


def create_main_window(study_file=None, mock=False):
    if not mock:
        return IntraAnalysisWindow(study_file)
    else:
        from morphologist.tests.mocks.main_window import MockIntraAnalysisWindow
        return MockIntraAnalysisWindow(study_file) 
