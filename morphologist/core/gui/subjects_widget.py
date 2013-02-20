import os

from morphologist.core.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.core.gui import ui_directory 


class SubjectsTableModel(QtCore.QAbstractTableModel):
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1 
    SUBJECTSTATUS_COL = 2
    header = ['group', 'name', 'status']

    def __init__(self, study_model, parent=None):
        super(SubjectsTableModel, self).__init__(parent)
        self._init_model(study_model)

    def _init_model(self, study_model):
        self._study_model = study_model
        self._study_model.status_changed.connect(\
                    self.on_study_model_status_changed)
        self._study_model.changed.connect(self.on_study_model_changed)

    def subject_from_row_index(self, index):
        return self._study_model.get_subject(index)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self._study_model.subject_count()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 3

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return
            elif orientation == QtCore.Qt.Horizontal:
                return self.header[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row, column = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            if column == SubjectsTableModel.GROUPNAME_COL:
                subject = self._study_model.get_subject(row)
                return subject.groupname
            if column == SubjectsTableModel.SUBJECTNAME_COL:
                subject = self._study_model.get_subject(row)
                return subject.name
            if column == SubjectsTableModel.SUBJECTSTATUS_COL:
                return self._study_model.get_status(row)

    @QtCore.Slot()                
    def on_study_model_status_changed(self):
        self._update_all_index()

    def _update_all_index(self):
        top_left = self.index(0, SubjectsTableModel.SUBJECTSTATUS_COL,
                              QtCore.QModelIndex())
        bottom_right = self.index(self.rowCount(),
                                  SubjectsTableModel.SUBJECTSTATUS_COL, 
                                  QtCore.QModelIndex())
        self.dataChanged.emit(top_left, bottom_right)

    @QtCore.Slot()                
    def on_study_model_changed(self):
        self.reset()


class SubjectsTableView(QtGui.QWidget):
    uifile = os.path.join(ui_directory, 'subjects_widget.ui')
    # FIXME : missing handling of sorting triangle icon
    header_style_sheet = '''
        QHeaderView::section {
            background-color: qlineargradient(x1:0 y1:0, x2:0 y2:1,
                                               stop:0 gray, stop:1 black);
            color:white;
            border: 0px
        }''' 

    def __init__(self, model, selection_model, parent=None):
        super(SubjectsTableView, self).__init__(parent)
        self.ui = loadUi(self.uifile, self)
        self._tableview = self.ui.subjects_tableview
        self._init_models(model, selection_model)
        self._init_widget()

    def _init_models(self, model, selection_model):
        self._tablemodel = model
        self._tableview.setModel(model)
        self._tableview.setSelectionModel(selection_model)
        self._tablemodel.modelReset.connect(self.on_modelReset)
        self.on_modelReset()
        
    def _init_widget(self):
        header = self._tableview.horizontalHeader()
        # FIXME : stylesheet has been disable and should stay disable until
        # subject list sorting has not been implementing
        #header.setStyleSheet(self.header_style_sheet)
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        
    @QtCore.Slot()
    def on_modelReset(self):
        self._tableview.selectRow(0)
        
