import os

from morphologist.core.study import Study
from morphologist.core.gui.qt_backend import QtGui, QtCore
from morphologist.core.gui.study_editor import StudyEditor


class StudyPropertiesEditorWidget(QtGui.QWidget):
    validity_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None,
                editor_mode=StudyEditor.NEW_STUDY):
        super(StudyPropertiesEditorWidget, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
        self._item_model = StudyPropertiesEditorItemModel(study_properties_editor, self)
        self._item_delegate = StudyPropertiesEditorItemDelegate(self)
        self._init_ui(parent, editor_mode)
        self._init_mapper()
        self.ui.link_button.toggled.connect(self.on_link_button_toggled)
        self._item_model.status_changed.connect(self.on_item_model_status_changed)
    
    # FIXME: better: move those widgets in a separate .ui
    def _init_ui(self, parent, editor_mode):
        # create dummy ui attribute
        self.ui = type('dummy UI', (QtGui.QWidget,), {})()
        self.ui.studyname_lineEdit = parent.ui.studyname_lineEdit
        self.ui.outputdir_lineEdit = parent.ui.outputdir_lineEdit
        self.ui.outputdir_button = parent.ui.outputdir_button
        self.ui.backup_filename_lineEdit = parent.ui.backup_filename_lineEdit
        self.ui.backup_filename_button = parent.ui.backup_filename_button
        self.ui.link_button = parent.ui.link_button
        self.ui.parameter_template_combobox = parent.ui.parameter_template_combobox
        if editor_mode == StudyEditor.EDIT_STUDY:
            self.ui.outputdir_lineEdit.setEnabled(False)
            self.ui.outputdir_button.setEnabled(False)
            self.ui.backup_filename_lineEdit.setEnabled(False)
            self.ui.backup_filename_button.setEnabled(False)
            self.ui.link_button.setEnabled(False)
            self.ui.parameter_template_combobox.setEnabled(False)
        self._create_parameter_template_combobox()

    def _create_parameter_template_combobox(self):
        parameter_templates = self._study_properties_editor.analysis_cls.PARAMETER_TEMPLATES
        for param_template in parameter_templates:
            param_template_name = param_template.name 
            self.ui.parameter_template_combobox.addItem(param_template_name)

    def _init_mapper(self):
        self._mapper = StudyPropertiesEditorWidgetMapper(self)
        # XXX: AutoSubmit used here, in order that commitData works/is enable
        self._mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self._mapper.setModel(self._item_model)        
        self._mapper.setItemDelegate(self._item_delegate)
        self._mapper.addMapping(self.ui.studyname_lineEdit, 0)
        self._mapper.addMapping(self.ui.outputdir_lineEdit, 1)
        self._mapper.addMapping(self.ui.backup_filename_lineEdit, 2)
        self._mapper.addMapping(self.ui.parameter_template_combobox, 3,
                                                        "currentText")
        self.ui.studyname_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.outputdir_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.backup_filename_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.parameter_template_combobox.currentIndexChanged.connect(self._mapper.submit)
        self.ui.outputdir_button.clicked.connect(self.on_outputdir_button_clicked)
        self.ui.backup_filename_button.clicked.connect(self.on_backup_filename_button_clicked)
        self._mapper.toFirst()

    @QtCore.Slot("bool")
    def on_item_model_status_changed(self, status):
        self.validity_changed.emit(status)

    @QtCore.Slot("bool")
    def on_link_button_toggled(self, checked):
        self._item_model.linked_inputs = (not checked)

    @QtCore.Slot()
    def on_outputdir_button_clicked(self):
        caption = 'Select study output directory'
        default_directory = self._study_properties_editor.outputdir
        if default_directory == '':
            default_directory = os.getcwd()
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                                caption, default_directory) 
        if selected_directory != '':
            self._item_model.set_data(\
                StudyPropertiesEditorItemModel.OUTPUTDIR_COL,
                selected_directory)

    @QtCore.Slot()
    def on_backup_filename_button_clicked(self):
        caption = 'Select study backup filename'
        default_filename = self._study_properties_editor.backup_filename
        if default_filename == '':
            default_filename = os.path.join(os.getcwd(), 'study.json')
        selected_filename = QtGui.QFileDialog.getSaveFileName(self.ui,
                                                caption, default_filename) 
        if selected_filename != '':
            self._item_model.set_data(\
                StudyPropertiesEditorItemModel.BACKUP_FILENAME_COL,
                selected_filename)


class StudyPropertiesEditorWidgetMapper(QtGui.QDataWidgetMapper):

    def __init__(self, parent=None):
        super(StudyPropertiesEditorWidgetMapper, self).__init__(parent)
 
    # overrided Qt method
    def submit(self):
        obj = self.sender()
        delegate = self.itemDelegate()
        model = self.model()
        if not model.isEdited():
            delegate.commitData.emit(obj)


class StudyPropertiesEditorItemDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(StudyPropertiesEditorItemDelegate, self).__init__(parent)
        
    # overrided Qt method
    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, QtCore.Qt.EditRole)
        property = editor.metaObject().userProperty().name()
        # don't update editor if not needed: fix cursor issue
        if value != editor.property(property):
            editor.setProperty(property, value)
        if model.is_data_colorable(index):
            bg_color = model.data(index, QtCore.Qt.BackgroundRole)
            style_sheet = '''
            QLineEdit { 
                background-color: %s;
                border: 1px solid grey;
                border-radius: 4px;
                padding: 2px;
                margin: 1px;
            }
            QLineEdit:focus {
                background-color: %s;
                border: 1px solid #ff7777;
                border-radius: 4px;
                padding: 2px;
                margin: 1px;
            }
        ''' % tuple([bg_color.name()] * 2)
            editor.setStyleSheet(style_sheet)
 

class StudyPropertiesEditorItemModel(QtCore.QAbstractItemModel):
    NAME_COL = 0
    OUTPUTDIR_COL = 1
    BACKUP_FILENAME_COL = 2
    PARAMETER_TEMPLATE_NAME_COL = 3
    attributes = ["name", "outputdir", "backup_filename", "parameter_template_name"]
    status_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None):
        super(StudyPropertiesEditorItemModel, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
        self.linked_inputs = True # model for the link button
        self._is_edited = False
        self._status = True # ok si 3 first attributes != ''

    # overrided Qt method
    def columnCount(self):
        return 4

    # overrided Qt method
    def rowCount(self, parent=QtCore.QModelIndex()):
        return 1

    # overrided Qt method
    def index(self, row, column, parent=QtCore.QModelIndex()):
        return self.createIndex(row, column, self)

    # overrided Qt method
    def parent(self, index=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

    # overrided Qt method
    def data(self, index, role=QtCore.Qt.DisplayRole):
        column = index.column()
        value = self._study_properties_editor.__getattribute__(self.attributes[column])
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return value
        elif role == QtCore.Qt.BackgroundRole:
            if column in [self.NAME_COL, self.OUTPUTDIR_COL,
                                self.BACKUP_FILENAME_COL]:
                if self._invalid_value(value):
                    return QtGui.QColor('#ffaaaa')
                else:
                    return QtGui.QColor('white')

    # overrided Qt method
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        self._is_edited = True
        column = index.column() 
        attribute = self.attributes[column]
        old_status = self._status
        if role != QtCore.Qt.EditRole: return
        self._study_properties_editor.__setattr__(attribute, value)
        self.dataChanged.emit(index, index)
        if self.linked_inputs:
            if column == self.OUTPUTDIR_COL:
                backup_filename = Study.default_backup_filename_from_outputdir(value)
                column_to_be_updated = self.BACKUP_FILENAME_COL
                attrib = self.attributes[column_to_be_updated]
                self._study_properties_editor.__setattr__(attrib, backup_filename)
                changed_index = self.index(index.row(), column_to_be_updated)
                self.dataChanged.emit(changed_index, changed_index)
            elif column == self.BACKUP_FILENAME_COL:
                outputdir = Study.default_outputdir_from_backup_filename(value)
                column_to_be_updated = self.OUTPUTDIR_COL
                attrib = self.attributes[column_to_be_updated]
                self._study_properties_editor.__setattr__(attrib, outputdir)
                changed_index = self.index(index.row(), column_to_be_updated)
                self.dataChanged.emit(changed_index, changed_index)
        self._is_edited = False
        self._status = not self._invalid_value(value) 
        if old_status != self._status:
            self.status_changed.emit(self._status)
        return True

    def is_data_colorable(self, index):
        column = index.column()
        return column in [self.NAME_COL, self.OUTPUTDIR_COL,
                                    self.BACKUP_FILENAME_COL]

    def set_data(self, col, value):
        row = 0
        index = self.index(row, col)
        return self.setData(index, value)

    def _invalid_value(self, value):
        return value == ''

    def isEdited(self):
        return self._is_edited

