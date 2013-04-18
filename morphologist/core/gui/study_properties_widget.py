import os

from morphologist.core.utils import create_filename_compatible_string
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
        self._item_model.status_changed.connect(self.on_item_model_status_changed)
    
    # FIXME: better: move those widgets in a separate .ui
    def _init_ui(self, parent, editor_mode):
        # create dummy ui attribute
        self.ui = type('dummy UI', (QtGui.QWidget,), {})()
        self.ui.studyname_lineEdit = parent.ui.studyname_lineEdit
        self.ui.outputdir_lineEdit = parent.ui.outputdir_lineEdit
        self.ui.outputdir_button = parent.ui.outputdir_button
        self.ui.parameter_template_combobox = parent.ui.parameter_template_combobox
        if editor_mode == StudyEditor.EDIT_STUDY:
            self.ui.outputdir_lineEdit.setEnabled(False)
            self.ui.outputdir_button.setEnabled(False)
            self.ui.parameter_template_combobox.setEnabled(False)
        self._create_parameter_template_combobox()

    def _create_parameter_template_combobox(self):
        parameter_templates = self._study_properties_editor.parameter_templates
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
        self._mapper.addMapping(self.ui.parameter_template_combobox, 2,
                                                        "currentIndex")
        self.ui.studyname_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.outputdir_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.parameter_template_combobox.currentIndexChanged.connect(self._mapper.submit)
        self.ui.outputdir_button.clicked.connect(self.on_outputdir_button_clicked)
        self._mapper.toFirst()

    @QtCore.Slot("bool")
    def on_item_model_status_changed(self, status):
        self.validity_changed.emit(status)

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


class StudyPropertiesEditorWidgetMapper(QtGui.QDataWidgetMapper):

    def __init__(self, parent=None):
        super(StudyPropertiesEditorWidgetMapper, self).__init__(parent)
 
    # overrided Qt method
    def submit(self):
        obj = self.sender()
        delegate = self.itemDelegate()
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
    PARAMETER_TEMPLATE_NAME_COL = 2
    attributes = ["name", "outputdir", "parameter_template_index"]
    status_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None):
        super(StudyPropertiesEditorItemModel, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
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
            if column in [self.NAME_COL, self.OUTPUTDIR_COL]:
                if self._invalid_value(value):
                    return QtGui.QColor('#ffaaaa')
                else:
                    return QtGui.QColor('white')

    # overrided Qt method
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        column = index.column() 
        old_status = self._status
        if role != QtCore.Qt.EditRole: return
        self._set_value(row, column, value)
        if (column == self.NAME_COL and 
            self._study_properties_editor.mode == StudyEditor.NEW_STUDY):
            outputdir = self._study_properties_editor.outputdir
            basedir = os.path.dirname(outputdir)
            new_basename = create_filename_compatible_string(value)
            new_value = os.path.join(basedir, new_basename)
            self._set_value(row, self.OUTPUTDIR_COL, new_value)
        self._status = not self._invalid_value(value) 
        if old_status != self._status:
            self.status_changed.emit(self._status)
        return True

    def _set_value(self, row, column, value):
        attrib = self.attributes[column]
        self._study_properties_editor.__setattr__(attrib, value)
        changed_index = self.index(row, column)
        self.dataChanged.emit(changed_index, changed_index)
        
    def is_data_colorable(self, index):
        column = index.column()
        return column in [self.NAME_COL, self.OUTPUTDIR_COL]

    def set_data(self, col, value):
        row = 0
        index = self.index(row, col)
        return self.setData(index, value)

    def _invalid_value(self, value):
        return value == ''

