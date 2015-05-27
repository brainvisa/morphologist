import os

from morphologist.core.constants import ALL_SUBJECTS
from morphologist.core.settings import settings
from morphologist.core.utils import FuncQThread
from morphologist.core.runner import SomaWorkflowRunner
from morphologist.core.study import Study, StudySerializationError
from morphologist.core.analysis import AnalysisFactory
from morphologist.core.gui.study_model import LazyStudyModel
from morphologist.core.gui.analysis_model import LazyAnalysisModel
from morphologist.core.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.core.gui.subjects_widget import SubjectsWidget
from morphologist.core.gui.runner_widget import RunnerView
from morphologist.core.gui.runner_settings_widget \
                        import RunnerSettingsDialog
from morphologist.core.gui.study_editor_widget import StudyEditorDialog, \
                                                      StudyEditor
from morphologist.core.gui.import_study_widget import ImportStudyDialog, \
                                                      ImportStudyEditorDialog
from morphologist.core.gui.import_subjects_widget import ImportSubjectsDialog
from morphologist.core.backends.mixins import ViewType
from morphologist.gui import ui_directory 
from morphologist.gui.viewport_widget import IntraAnalysisViewportModel,\
                                             IntraAnalysisViewportWidget
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames


ApplicationStudy = None # dynamically defined


class ActionHandler(QtCore.QObject):
    terminated = QtCore.pyqtSignal()

    def start(self):
        clsname = self.__class__.__name__
        raise NotImplementedError('%s is an abstract class' % clsname)


class StudyActionHandler(ActionHandler):
    study_updated = QtCore.pyqtSignal(Study)

    def __init__(self, parent=None):
        super(StudyActionHandler, self).__init__(parent)
        self._study_editor_dialog = None
        self._import_subjects_dialog = None
        self._create_updated_study_thread = None

    @QtCore.Slot()
    def _on_study_dialog_accepted(self):
        study_editor = self._study_editor_dialog.study_editor
        self._study_editor_dialog = None
        self._create_updated_study_thread = FuncQThread(\
                    study_editor.create_updated_study)
        if study_editor.subjects_editor.has_subjects_to_be_imported():
            dialog = ImportSubjectsDialog(study_editor, parent=self.parent())
            dialog.ui.accepted.connect(self._on_import_subjects_dialog_accepted)
            dialog.show()
            self._import_subjects_dialog = dialog
            self._create_updated_study_thread.finished.connect(\
                self._on_create_updated_study_thread_finished)
        else:
            self._create_updated_study_thread.finished.connect(\
                self._on_create_updated_study_thread_finished_without_dialog)
        self._create_updated_study_thread.start()

    @QtCore.Slot()
    def _on_create_updated_study_thread_finished_without_dialog(self):
        self._on_create_updated_study_thread_finished()
        self._on_import_subjects_dialog_accepted()

    @QtCore.Slot()
    def _on_create_updated_study_thread_finished(self):
        study = self._create_updated_study_thread.res
        self.study_updated.emit(study)
        self._create_updated_study_thread = None

    @QtCore.Slot()
    def _on_import_subjects_dialog_accepted(self):
        self._import_subjects_dialog = None
        self.terminated.emit()


class NewStudyActionHandler(StudyActionHandler):

    def __init__(self, analysis_type, parent=None):
        super(NewStudyActionHandler, self).__init__(parent)
        self._analysis_type = analysis_type

    def start(self):
        study = ApplicationStudy(self._analysis_type)
        dialog = StudyEditorDialog(study, parent=self.parent(),
                            editor_mode=StudyEditor.NEW_STUDY)
        dialog.ui.accepted.connect(self._on_study_dialog_accepted)
        dialog.ui.show()
        self._study_editor_dialog = dialog


class EditStudyActionHandler(StudyActionHandler):

    def __init__(self, study, parent=None):
        super(EditStudyActionHandler, self).__init__(parent)
        self._study = study

    def start(self):
        dialog = StudyEditorDialog(self._study, parent=self.parent(),
                                    editor_mode=StudyEditor.EDIT_STUDY)
        dialog.ui.accepted.connect(self._on_study_dialog_accepted)
        dialog.ui.show()
        self._study_editor_dialog = dialog


class EditImportedStudyActionHandler(StudyActionHandler):

    def __init__(self, study, analysis_type, subjects,
                    import_data_in_place, parent=None):
        super(EditImportedStudyActionHandler, self).__init__(parent)
        self._study = study
        self._import_data_in_place = import_data_in_place
        self._analysis_type = analysis_type
        self._subjects = subjects

    def start(self):
        dialog = ImportStudyEditorDialog(self._study, self.parent(),
                        self._import_data_in_place, self._subjects)
        dialog.ui.accepted.connect(self._on_study_dialog_accepted)
        dialog.ui.show()
        self._study_editor_dialog = dialog


class ImportStudyActionHandler(ActionHandler):
    study_updated = QtCore.pyqtSignal(Study)

    def __init__(self, analysis_type, parent=None):
        super(ImportStudyActionHandler, self).__init__(parent)
        self._analysis_type = analysis_type
        self._import_study_dialog = None
        self._edit_imported_study_action_handler = None

    def start(self):
        analysis_cls = AnalysisFactory.get_analysis_cls(self._analysis_type)
        parameter_template_name = analysis_cls.get_default_parameter_template_name()
        dialog = ImportStudyDialog(self.parent(),
                ApplicationStudy.default_output_directory, self._analysis_type,
                selected_template_name=parameter_template_name)
        dialog.accepted.connect(self._on_import_study_dialog_accepted)
        dialog.show()
        self._import_study_dialog = dialog
        
    @QtCore.Slot()
    def _on_import_study_dialog_accepted(self):
        dialog = self._import_study_dialog
        import_data_in_place = dialog.is_import_in_place_selected()
        if import_data_in_place:
            organized_directory = dialog.get_organized_directory()
            parameter_template_name = dialog.get_parameter_template_name()
            study = ApplicationStudy.from_organized_directory(\
                                            self._analysis_type,
                                            organized_directory,
                                            parameter_template_name)
            subjects = None
        else:
            study = ApplicationStudy(self._analysis_type)
            subjects = dialog.get_subjects()
        self._edit_imported_study_action_handler = \
                EditImportedStudyActionHandler(study, self._analysis_type,
                                        subjects, import_data_in_place)
        self._edit_imported_study_action_handler.terminated.connect(\
            self._on_edit_imported_study_action_handler_terminated)
        self._edit_imported_study_action_handler.study_updated.connect(\
            self._on_edit_imported_study_action_handler_study_updated)
        self._edit_imported_study_action_handler.start()

    @QtCore.Slot()
    def _on_edit_imported_study_action_handler_terminated(self):
        self.terminated.emit()
        self._edit_imported_study_action_handler = None

    @QtCore.Slot(Study)
    def _on_edit_imported_study_action_handler_study_updated(self, study):
        self.study_updated.emit(study)
        

class MainWindow(QtGui.QMainWindow):
    uifile = os.path.join(ui_directory, 'main_window.ui')

    def _init_class(self):
        global ApplicationStudy
        if settings.tests.mock:
            from morphologist.core.tests.mocks.study import MockStudy
            ApplicationStudy = MockStudy
        else:
            ApplicationStudy = Study

    def __init__(self, analysis_type, study_directory=None, 
            import_study=False):
        super(MainWindow, self).__init__()
        if ApplicationStudy is None: self._init_class()
        self.ui = loadUi(self.uifile, self)
        toolbar_action_group = QtGui.QActionGroup(self)
        toolbar_action_group.addAction(self.ui.action_axial_view)
        toolbar_action_group.addAction(self.ui.action_coronal_view)

        self._init_action_handlers()
        self._analysis_type = analysis_type
        self.study = ApplicationStudy(self._analysis_type)
        self.runner = self._create_runner(self.study)
        self.study_model = LazyStudyModel(self.study, self.runner)
        self.analysis_model = LazyAnalysisModel()

        self.viewport_model = IntraAnalysisViewportModel(self.analysis_model)
        self.viewport_widget = IntraAnalysisViewportWidget(self.viewport_model, self)
        self.setCentralWidget(self.viewport_widget)
        
        self.study_view = SubjectsWidget(self.study_model)
        self.ui.study_widget_dock.setWidget(self.study_view)
        
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)

        self.runner_view = RunnerView(self.study_model)
        self.ui.runner_widget_dock.setWidget(self.runner_view)

        self.setWindowTitle(self._window_title())
        self.dialogs = {}
        
        self.study_model.current_subject_changed.connect(self.on_current_subject_changed)
        self.on_current_subject_changed()
        if study_directory is not None:
            if import_study:
                self._create_inplace_study(study_directory, 'brainvisa')
            else:
                self._try_open_study_from_directory(study_directory)

    def _init_action_handlers(self):
        self._new_study_action_handler = None
        self._import_study_action_handler = None
        self._edit_study_action_handler = None

    def _try_open_study_from_directory(self, study_directory):
        try:
            study = ApplicationStudy.from_study_directory(study_directory)
        except StudySerializationError, e:
            title = "Cannot load study"
            msg = "'%s':\n%s" % (study_directory, e)
            QtGui.QMessageBox.critical(self, title, msg)
        else:
            self.set_study(study)

    def _create_inplace_study(self, study_directory, parameter_template_name):
        study = ApplicationStudy.from_organized_directory(\
                                        self._analysis_type,
                                        study_directory,
                                        parameter_template_name)
        self.set_study(study)
        study.save_to_backup_file()

    def _create_runner(self, study):
        return SomaWorkflowRunner(study)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_new_study_triggered(self):
        msg = 'Stop current running analysis and create a new study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        self._new_study_action_handler = NewStudyActionHandler(\
                                        self._analysis_type, self)
        self._new_study_action_handler.study_updated.connect(\
            self.on_study_action_handler_study_updated)
        self._new_study_action_handler.start()
       
    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_import_study_triggered(self):
        msg = 'Stop current running analysis and import a study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        self._import_study_action_handler = ImportStudyActionHandler(\
                                             self._analysis_type, self)
        self._import_study_action_handler.study_updated.connect(\
            self.on_study_action_handler_study_updated)
        self._import_study_action_handler.start()
   
    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_edit_study_triggered(self):
        msg = 'Stop current running analysis and edit the current study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        self._edit_study_action_handler = EditStudyActionHandler(self.study,
                                                                    self)
        self._edit_study_action_handler.study_updated.connect(\
            self.on_study_action_handler_study_updated)
        self._edit_study_action_handler.start()

    @QtCore.Slot(Study)
    def on_study_action_handler_study_updated(self, study):
        self.set_study(study)
        self._try_save_to_backup_file()

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_open_study_triggered(self):
        msg = 'Stop current running analysis and open a study ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        study_directory = QtGui.QFileDialog.getExistingDirectory(parent=self.ui,
                                caption="Open a study directory", directory="", 
                                options=QtGui.QFileDialog.DontUseNativeDialog)
        if study_directory:
            self._try_open_study_from_directory(study_directory)

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

    def _try_save_to_backup_file(self):
        try:
            self.study.save_to_backup_file()
        except StudySerializationError, e:
            QtGui.QMessageBox.critical(self, "Cannot save the study", "%s" %(e))

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_export_morphometry_triggered(self):
        self.save_morphometry(ALL_SUBJECTS)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_export_selection_morphometry_triggered(self):
        subject_ids = self.study_model.get_selected_subject_ids()
        self.save_morphometry(subject_ids)

    def save_morphometry(self, subject_ids):
        msg = 'Stop current running analysis and save ' + \
              'availables morphometry data ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): return
        filter = 'CSV (*.csv)'
        morphometry_filepath = QtGui.QFileDialog.getSaveFileName(self.ui,
                    caption="Choose morphometry output file", directory="",
                    options=QtGui.QFileDialog.DontUseNativeDialog,
                    filter=filter)
        if morphometry_filepath == '': return
        if subject_ids is ALL_SUBJECTS:
            subject_ids = self.study.subjects.iterkeys()
        command = ['python', '-m',
                   'morphologist.intra_analysis.commands.morphometry-concat',
                   '-o', morphometry_filepath]
        for subject_id in subject_ids:
            analysis = self.study.analyses[subject_id]
            for csv_filepath in [\
                analysis.outputs[IntraAnalysisParameterNames.LEFT_NATIVE_MORPHOMETRY_CSV],
                analysis.outputs[IntraAnalysisParameterNames.RIGHT_NATIVE_MORPHOMETRY_CSV],
                analysis.outputs[IntraAnalysisParameterNames.LEFT_NORMALIZED_MORPHOMETRY_CSV],
                analysis.outputs[IntraAnalysisParameterNames.RIGHT_NORMALIZED_MORPHOMETRY_CSV]]:
            # ignore none-existing files
                if os.path.isfile(csv_filepath):
                    command.append(csv_filepath)
        os.system(' '.join(command))

    @QtCore.Slot()
    def on_current_subject_changed(self):
        subject_id = self.study_model.get_current_subject_id()
        if subject_id:
            analysis = self.study.analyses[subject_id]
            self.analysis_model.set_analysis(analysis)

    def set_study(self, study):
        self.study = study
        self.runner = self._create_runner(self.study)
        self.study_model.set_study_and_runner(self.study, self.runner)
        if not self.study.has_subjects():
            self.analysis_model.remove_analysis()
        self.setWindowTitle(self._window_title())

    def _window_title(self):
        title = "Morphologist - %s" % self.study.name
        if settings.tests.mock:
            title += "--- MOCK MODE ---"
        return title
    
    def closeEvent(self, event):
        msg = 'Stop current running analysis and quit ?'
        if self._runner_still_running_after_stopping_asked_to_user(msg): 
            event.ignore()
        else:
            event.accept()

    # this slot is automagically connected
    @QtCore.Slot()
    def on_action_runner_settings_triggered(self):
        dialog = RunnerSettingsDialog(settings, self)
        dialog.show()
    
    # this slot is automagically connected
    @QtCore.Slot(bool)        
    def on_action_axial_view_toggled(self, checked):
        if checked:
            self.viewport_widget.set_object3d_views_view_type(ViewType.AXIAL)

    # this slot is automagically connected
    @QtCore.Slot(bool)        
    def on_action_coronal_view_toggled(self, checked):
        if checked:
            self.viewport_widget.set_object3d_views_view_type(ViewType.CORONAL)
