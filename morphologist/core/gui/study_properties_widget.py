import os
import traits.api as traits

from morphologist.core.utils import create_filename_compatible_string
from morphologist.core.gui.qt_backend import QtGui, QtCore
from morphologist.core.gui.study_editor import StudyEditor


class StudyPropertiesEditorWidget(QtGui.QWidget):
    validity_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None,
                editor_mode=StudyEditor.NEW_STUDY):
        super(StudyPropertiesEditorWidget, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
        self._item_model \
            = StudyPropertiesEditorItemModel(study_properties_editor, self)
        self._item_delegate = StudyPropertiesEditorItemDelegate(self)
        self._init_ui(parent, editor_mode)
        self._init_mapper()
        self._item_model.status_changed.connect(
            self.on_item_model_status_changed)

    # FIXME: better: move those widgets in a separate .ui
    def _init_ui(self, parent, editor_mode):
        # create dummy ui attribute
        self.ui = type('dummy UI', (QtGui.QWidget,), {})()
        self.ui.studyname_lineEdit = parent.ui.studyname_lineEdit
        self.ui.output_directory_lineEdit = parent.ui.output_directory_lineEdit
        self.ui.output_directory_button = parent.ui.output_directory_button
        self.ui.volume_format_combobox = parent.ui.volume_format_combobox
        self.ui.mesh_format_combobox = parent.ui.mesh_format_combobox
        #self.ui.spm_standalone_checkbox = parent.ui.spm_standalone_checkbox
        #self.ui.spm_exec_lineedit = parent.ui.spm_exec_lineedit
        #self.ui.spm_exec_button = parent.ui.spm_exec_button
        self.ui.computing_resource_combobox \
            = parent.ui.computing_resource_combobox
        if editor_mode == StudyEditor.EDIT_STUDY:
            self.ui.output_directory_lineEdit.setEnabled(False)
            self.ui.output_directory_button.setEnabled(False)
        self._create_format_comboboxes()
        self._create_computing_resources_combobox()

    def _create_format_comboboxes(self):
        for format_name in self._study_properties_editor.volumes_formats:
            self.ui.volume_format_combobox.addItem(format_name)
        for format_name in self._study_properties_editor.meshes_formats:
            self.ui.mesh_format_combobox.addItem(format_name)

    def _create_computing_resources_combobox(self):
        for resource_name \
                in self._study_properties_editor.available_computing_resources:
            self.ui.computing_resource_combobox.addItem(resource_name)

    def _init_mapper(self):
        self._mapper = StudyPropertiesEditorWidgetMapper(self)
        # XXX: AutoSubmit used here, in order that commitData works/is enable
        self._mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        self._mapper.setModel(self._item_model)
        self._mapper.setItemDelegate(self._item_delegate)
        self._mapper.addMapping(self.ui.studyname_lineEdit,
                                StudyPropertiesEditorItemModel.NAME_COL)
        self._mapper.addMapping(self.ui.output_directory_lineEdit,
                                StudyPropertiesEditorItemModel.OUTPUTDIR_COL)
        self._mapper.addMapping(
            self.ui.volume_format_combobox,
            StudyPropertiesEditorItemModel.VOLUME_FORMAT_COL,
            "currentIndex")
        self._mapper.addMapping(self.ui.mesh_format_combobox,
                                StudyPropertiesEditorItemModel.MESH_FORMAT_COL,
                                "currentIndex")
        #self._mapper.addMapping(self.ui.spm_standalone_checkbox, 4, "checked")
        #self._mapper.addMapping(self.ui.spm_exec_lineedit, 5)
        self._mapper.addMapping(
            self.ui.computing_resource_combobox,
            StudyPropertiesEditorItemModel.COMPUTING_RESOURCE_COL,
            "currentIndex")

        self.ui.studyname_lineEdit.textChanged.connect(self._mapper.submit)
        self.ui.output_directory_lineEdit.textChanged.connect(
            self._mapper.submit)
        self.ui.output_directory_button.clicked.connect(
            self.on_output_directory_button_clicked)
        self.ui.volume_format_combobox.currentIndexChanged.connect(
            self._mapper.submit)
        self.ui.mesh_format_combobox.currentIndexChanged.connect(
            self._mapper.submit)
        #self.ui.spm_standalone_checkbox.stateChanged.connect(
            #self._mapper.submit)
        #self.ui.spm_exec_lineedit.textChanged.connect(self._mapper.submit)
        #self.ui.spm_exec_button.clicked.connect(
            #self.on_spm_exec_button_clicked)
        self.ui.computing_resource_combobox.currentIndexChanged.connect(
            self._mapper.submit)
        self._mapper.toFirst()

    @QtCore.Slot("bool")
    def on_item_model_status_changed(self, status):
        self.validity_changed.emit(status)

    @QtCore.Slot()
    def on_output_directory_button_clicked(self):
        caption = 'Select study output directory'
        default_directory = self._study_properties_editor.output_directory
        if default_directory == '':
            default_directory = os.getcwd()
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                                caption, default_directory) 
        if selected_directory != '':
            self._item_model.set_data(\
                StudyPropertiesEditorItemModel.OUTPUTDIR_COL,
                selected_directory)

    #@QtCore.Slot()
    #def on_spm_exec_button_clicked(self):
        #caption = 'Select SPM standalone executable'
        #if self._study_properties_editor.spm_exec \
                #and self._study_properties_editor.spm_exec \
                    #is not traits.Undefined:
            #default_directory = os.path.dirname(
                #self._study_properties_editor.spm_exec)
        #else:
            #default_directory = ''
        #selected_file = QtGui.QFileDialog.getOpenFileName(
            #self.ui, caption, default_directory)
        #if selected_file != '':
            #self._item_model.set_data(\
                #StudyPropertiesEditorItemModel.SPM_EXEC_COL,
                #selected_file)


class StudyPropertiesEditorWidgetMapper(QtGui.QDataWidgetMapper):

    def __init__(self, parent=None):
        super(StudyPropertiesEditorWidgetMapper, self).__init__(parent)

    # overrided Qt method
    def submit(self):
        obj = self.sender()
        if isinstance(obj, QtCore.QAbstractItemModel):
            obj = obj.widget()
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
    VOLUME_FORMAT_COL = 2
    MESH_FORMAT_COL = 3
    #SPM_STANDALONE_COL = 4
    #SPM_EXEC_COL = 5
    COMPUTING_RESOURCE_COL = 4
    attributes = ["study_name", "output_directory",
                  "volumes_format_index", "meshes_format_index",
                  #"spm_standalone", "spm_exec",
                  "computing_resource_index"]
    status_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None):
        super(StudyPropertiesEditorItemModel, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
        self._status = True # ok si 3 first attributes != ''

    # overrided Qt method
    def columnCount(self):
        return 5

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
        try:
            value = self._study_properties_editor.__getattribute__(
                self.attributes[column])
        except IndexError as e:
            import traceback, sys
            print 'index:', index
            print 'column:', column
            print e
            traceback.print_stack(file=sys.stdout)
            raise
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return value
        elif role == QtCore.Qt.BackgroundRole:
            if column in [self.NAME_COL, self.OUTPUTDIR_COL,
                          #self.SPM_EXEC_COL
                          ]:
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
            output_directory = self._study_properties_editor.output_directory
            basedir = os.path.dirname(output_directory)
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
        return column in [self.NAME_COL, self.OUTPUTDIR_COL,
                          #self.SPM_EXEC_COL
                          ]

    def set_data(self, col, value):
        row = 0
        index = self.index(row, col)
        return self.setData(index, value)

    def _invalid_value(self, value):
        return value == ''

    def widget(self):
        return self._study_properties_editor

