import os

from .qt_backend import QtCore, QtGui, loadUi
from .gui import ui_directory 
from ..study import Study
from .manage_study import ManageStudyWindow

class StudyTableModel(QtCore.QAbstractTableModel):
    SUBJECTNAME_COL = 0

    def __init__(self, study, parent=None):
        super(StudyTableModel, self).__init__(parent)
        self._study = None
        self._subjectnames = None
        self._set_study(study)
        self._header = ['name'] #TODO: to be extended

    def _set_study(self, study):
        self._study = study
        self._subjectnames = study.list_subject_names()

    def subjectname_from_row_index(self, index):
        return self._subjectnames[index]

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._study.subjects)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1 #TODO: to be extended

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return
            elif orientation == QtCore.Qt.Horizontal:
                return self._header[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row, column = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == StudyTableModel.SUBJECTNAME_COL:
                return self._subjectnames[row]


class StudyWidget(object):
    uifile = os.path.join(ui_directory, 'display_study.ui')
    header_style_sheet = '''
        QHeaderView::section {
            background-color: qlineargradient( x1:0 y1:0, x2:0 y2:1,
                                               stop:0 gray, stop:1 black);
            color:white;
            border: 0px
        }'''
    subjectname_column_width = 100    

    def __init__(self, study_tablemodel, parent=None):
        self.ui = loadUi(self.uifile, parent)
        self.study_tablemodel = study_tablemodel
        self.study_tableview = self.ui.widget()
        self.study_tableview.setModel(self.study_tablemodel)
        self.selection_model = self.study_tableview.selectionModel()

        self._init_ui()

    def _init_ui(self):
        header = self.study_tableview.horizontalHeader()
        header.setStyleSheet(self.header_style_sheet)
        header.resizeSection(0, self.subjectname_column_width)
        self.study_tableview.selectRow(0)


class IntraAnalysisWindow(object):
    uifile = os.path.join(ui_directory, 'intra_analysis.ui')

    def __init__(self, study):
        self.ui = loadUi(self.uifile)
        self.study = study
        self.study_tablemodel = StudyTableModel(self.study)
        self.study_widget = StudyWidget(self.study_tablemodel, self.ui.study_widget_dock)
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
        self.ui.setEnabled(True) #FIXME

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
        study = Study()
        manage_study_window = ManageStudyWindow(study)
        if (manage_study_window.ui.exec_() == QtGui.QDialog.Accepted):
            self.set_study(study)
        
    @QtCore.Slot()
    def on_open_study_action(self):
        # TODO : open a study from a file
        pass

    @QtCore.Slot()
    def on_save_study_action(self):
        # TODO : save a study in a file
        pass

    @QtCore.Slot("QModelIndex &, QModelIndex &")
    def on_selection_changed(self, current, previous):
        subjectname = self.study_tablemodel.subjectname_from_row_index(\
                                                        current.row())
        self.set_current_subjectname(subjectname)

    def set_study(self, study):
        self.study = study
        self.study_tablemodel = StudyTableModel(self.study)
        self.study_widget.study_tableview.setModel(self.study_tablemodel)
        self.ui.setWindowTitle("Morphologist - %s" % self.study.name)
        
    def set_current_subjectname(self, subjectname):
        self._current_subjectname = subjectname
        # TODO : update image


def create_main_window(study):
    return IntraAnalysisWindow(study)
