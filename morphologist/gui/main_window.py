import os

from .qt_backend import QtCore, QtGui, loadUi
from .gui import ui_directory 
from morphologist.study import Study
from morphologist.study import StudySerializationError
from .manage_study import ManageStudyWindow
from morphologist.intra_analysis import IntraAnalysis


class StudyTableModel(QtCore.QAbstractTableModel):
    SUBJECTNAME_COL = 0 
    SUBJECTSTATUS_COL = 1

    def __init__(self, study, parent=None):
        super(StudyTableModel, self).__init__(parent)
        self._study = None
        self._subjectnames = None
        self.set_study(study)
        self._header = ['name', 'status'] #TODO: to be extended

    def set_study(self, study):
        self.beginResetModel()
        self._study = study
        self._subjectnames = study.list_subject_names()
        self.endResetModel()

    def subjectname_from_row_index(self, index):
        return self._subjectnames[index]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._study.subjects)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2 #TODO: to be extended

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return
            elif orientation == QtCore.Qt.Horizontal:
                return self._header[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        # FIXME efficiency
        row, column = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == StudyTableModel.SUBJECTNAME_COL:
                return self._subjectnames[row]
            if column == StudyTableModel.SUBJECTSTATUS_COL:
                analysis = self._study.analysis[self._subjectnames[row]]
                if analysis.is_running():
                    return "is running"
                if analysis.last_run_failed():
                    return "last run failed"
                if len(analysis.output_params.list_existing_files()) == 0:
                    return "no output files"
                if len(analysis.output_params.list_missing_files()) == 0:
                    return "output files exist"
                return "some output files exist"


class StudyWidget(object):
    uifile = os.path.join(ui_directory, 'display_study.ui')
    # FIXME : missing handling of sorting triangle icon
    header_style_sheet = '''
        QHeaderView::section {
            background-color: qlineargradient( x1:0 y1:0, x2:0 y2:1,
                                               stop:0 gray, stop:1 black);
            color:white;
            border: 0px
        }'''
    subjectname_column_width = 100    

    def __init__(self, study, parent=None):
        self.ui = loadUi(self.uifile, parent)
        self.study_tableview = self.ui.widget()
        self.study_tablemodel = StudyTableModel(study)
        self.study_tableview.setModel(self.study_tablemodel)
        self.selection_model = self.study_tableview.selectionModel()

        self._init_ui()

    def _init_ui(self):
        header = self.study_tableview.horizontalHeader()
        # FIXME : stylesheet has been disable and should stay disable until
        # subject list sorting has not been implementing
        #header.setStyleSheet(self.header_style_sheet)
        header.resizeSection(0, self.subjectname_column_width)

    def set_study(self, study):
        self.study_tablemodel.set_study(study)
        self.study_tableview.selectRow(0)

class IntraAnalysisWindow(object):
    uifile = os.path.join(ui_directory, 'intra_analysis.ui')

    def __init__(self, study_file=None):
        self.ui = loadUi(self.uifile)
        self.study = self._create_study(study_file)

        self.study_widget = StudyWidget(self.study, self.ui.study_widget_dock)
        self.manage_study_window = None
        self._current_subjectname = None
        self._init_qt_connections()
        self._init_ui()

    def _init_qt_connections(self):
        self.ui.run_button.clicked.connect(self.on_run_button_clicked)
        self.ui.stop_button.clicked.connect(self.on_stop_button_clicked)
        self.ui.action_new_study.triggered.connect(self.on_new_study_action)
        self.ui.action_open_study.triggered.connect(self.on_open_study_action)
        self.ui.action_save_study.triggered.connect(self.on_save_study_action)
        self.study_widget.selection_model.currentChanged.connect(self.on_selection_changed)

    def _init_ui(self):
        # FIXME : should be true or false at the opening of the UI ?
        self.ui.setEnabled(True)


    def _create_study(self, study_file=None):
        if study_file:
          study = Study.from_file(study_file)
          study.clear_results()
          return study
        else:
          return Study()

    @QtCore.Slot()
    def on_run_button_clicked(self):
        self.ui.run_button.setEnabled(False)
        self.study.run_analyses()
        self.ui.stop_button.setEnabled(True)

    @QtCore.Slot()
    def on_stop_button_clicked(self):
        self.ui.stop_button.setEnabled(False)
        self.study.stop_analyses()
        self.ui.run_button.setEnabled(True)

    @QtCore.Slot()
    def on_new_study_action(self):
        study = self._create_study()
        self.manage_study_window = ManageStudyWindow(study, self.ui)
        self.manage_study_window.ui.accepted.connect(self.on_study_dialog_accepted)
        self.manage_study_window.ui.show()
        
    @QtCore.Slot()
    def on_study_dialog_accepted(self):
        # TODO : what to do with this commented line ?
        #study.set_analysis_parameters(IntraAnalysis.DEFAULT_PARAM_TEMPLATE)
        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        study = self.manage_study_window.study
        study.import_data(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)
        study.set_analysis_parameters(IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)
        self.set_study(study)
        self.manage_study_window = None
        QtGui.QApplication.restoreOverrideCursor()
        msgbox = QtGui.QMessageBox( QtGui.QMessageBox.Information, "Images importation", 
                                    "The images have been copied in %s directory." % study.outputdir, 
                                    QtGui.QMessageBox.Ok, self.ui)
        msgbox.show()
        

    @QtCore.Slot()
    def on_open_study_action(self):
        filename = QtGui.QFileDialog.getOpenFileName(self.ui)
        if filename:
            try:
                study = self._create_study(filename)
            except StudySerializationError, e:
                QtGui.QMessageBox.critical(self.ui, 
                                          "Cannot load the study", "%s" %(e))
            else:
                self.set_study(study) 

    @QtCore.Slot()
    def on_save_study_action(self):
        filename = QtGui.QFileDialog.getSaveFileName(self.ui)
        if filename:
            try:
                self.study.save_to_file(filename)
            except StudySerializationError, e:
                QtGui.QMessageBox.critical(self.ui, 
                                          "Cannot save the study", "%s" %(e))
            

    @QtCore.Slot("QModelIndex &, QModelIndex &")
    def on_selection_changed(self, current, previous):
        subjectname = self.study_widget.study_tablemodel.subjectname_from_row_index(\
                                                        current.row())
        self.set_current_subjectname(subjectname)

    def set_study(self, study):
        self.study = study
        self.study_widget.set_study(self.study)
        self.ui.setWindowTitle("Morphologist - %s" % self.study.name)
        
    def set_current_subjectname(self, subjectname):
        self._current_subjectname = subjectname
        # TODO : update image


