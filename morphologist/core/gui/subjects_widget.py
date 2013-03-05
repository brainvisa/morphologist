import os

from morphologist.core.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.core.gui import ui_directory

 
class SubjectsWidget(QtGui.QWidget):

    def __init__(self, model, parent=None):
        super(SubjectsWidget, self).__init__(parent)
        self._tableview = SubjectsTableView(model, self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self._tableview)
        self.setLayout(layout)       
        
        
class SubjectsTableView(QtGui.QTableView):
    uifile = os.path.join(ui_directory, 'subjects_widget.ui')
    
    def __init__(self, model, parent=None):
        super(SubjectsTableView, self).__init__(parent)
        self._init_widget()
        self._init_model(model)
        
    def _init_model(self, model):
        self._study_model = model
        self._tablemodel = SubjectsTableModel(model)
        self.setModel(self._tablemodel)
        
    def _init_widget(self):
        self.ui = loadUi(self.uifile, self)
        header = self.horizontalHeader()
        header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setItemDelegate(SubjectsItemDelegate())
        #self.setStyleSheet("QTableView {selection-background-color: yellow}")

    def selectionCommand(self, index, event):
        row, column = index.row(), index.column()
        table_model = self.model()
        if column != table_model.SELECTION_COL:
            self._study_model.set_current_subject_index(row)
            return QtGui.QItemSelectionModel.NoUpdate
        flags = super(SubjectsTableView, self).selectionCommand(index, event)
        if flags & QtGui.QItemSelectionModel.Clear and flags & QtGui.QItemSelectionModel.Select:
            flags |= QtGui.QItemSelectionModel.Toggle
            flags &= ~QtGui.QItemSelectionModel.ClearAndSelect
        else:
            flags &= ~QtGui.QItemSelectionModel.Clear
        return flags
        
    def selectionChanged(self, selected, deselected):
        self._set_selected_indexes(selected.indexes(), True)
        self._set_selected_indexes(deselected.indexes(), False)
    
    def _set_selected_indexes(self, indexes, selected):
        for index in indexes:
            row_index = index.row()
            self._study_model.set_selected_subject(row_index, selected)   
            
         
class SubjectsItemDelegate(QtGui.QStyledItemDelegate):
    
    def paint(self, painter, option, index):
        option.state = option.state & ~QtGui.QStyle.State_Selected
        super(SubjectsItemDelegate, self).paint(painter, option, index)
            
    
class SubjectsTableModel(QtCore.QAbstractTableModel):
    SELECTION_COL = 0
    GROUPNAME_COL = 1
    SUBJECTNAME_COL = 2 
    SUBJECTSTATUS_COL = 3
    header = ['', 'group', 'name', 'status']

    def __init__(self, study_model, parent=None):
        super(SubjectsTableModel, self).__init__(parent)
        self._init_model(study_model)

    def _init_model(self, study_model):
        self._study_model = study_model
        self._study_model.status_changed.connect(\
                    self.on_study_model_status_changed)
        self._study_model.changed.connect(self.on_study_model_changed)
        self._study_model.current_subject_changed.connect(self.on_current_subject_changed)
        self._study_model.subject_selection_changed.connect(self.on_subject_changed)

    def subject_from_row_index(self, index):
        return self._study_model.get_subject(index)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self._study_model.subject_count()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.header[section]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row, column = index.row(), index.column()
        if role == QtCore.Qt.DisplayRole:
            subject = self._study_model.get_subject(row)
            if column == SubjectsTableModel.GROUPNAME_COL:
                return subject.groupname
            if column == SubjectsTableModel.SUBJECTNAME_COL:
                return subject.name
            if column == SubjectsTableModel.SUBJECTSTATUS_COL:
                return self._study_model.get_status(row)
        elif role == QtCore.Qt.BackgroundRole:
            if row == self._study_model.get_current_subject_index():
                return QtGui.QApplication.palette().highlight()
            elif self._study_model.is_selected_subject(row):
                return QtGui.QApplication.palette().alternateBase()
        elif role == QtCore.Qt.CheckStateRole:
            if column == self.SELECTION_COL:
                if self._study_model.is_selected_subject(row):
                    return QtCore.Qt.Checked
                return QtCore.Qt.Unchecked
             
    def flags(self, index):
        column = index.column()
        flags = super(SubjectsTableModel, self).flags(index)
        if column == self.SELECTION_COL:
            flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        return flags
        
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

    @QtCore.Slot() 
    def on_current_subject_changed(self):
        row = self._study_model.get_current_subject_index()
        self.on_subject_changed(row)
    
    @QtCore.Slot(int)     
    def on_subject_changed(self, row):
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount()))

