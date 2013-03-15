import os
import urllib
import zipfile
import shutil
import tempfile
import numpy
from collections import namedtuple

from morphologist.core.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.core.gui import ui_directory
from morphologist.core.study import Study, Subject
from morphologist.core.formats import FormatsManager
from morphologist.core.analysis import ImportationError


class StudyEditor(object):
    # study edition mode
    NEW_STUDY = 0
    EDIT_STUDY = 1
    # update policy
    ON_SUBJECT_REMOVED_DELETE_FILES = 0
    ON_SUBJECT_REMOVED_DO_NOTHING = 1

    def __init__(self, study, mode=NEW_STUDY,
        study_update_policy=ON_SUBJECT_REMOVED_DO_NOTHING):
        self.study = study
        self.study_update_policy = study_update_policy 
        self._study_properties_editor = StudyPropertiesEditor(study)
        self._subjects_editor = SubjectsEditor(study)
        self.mode = mode

    @property
    def subjects_editor(self):
        return self._subjects_editor

    @property
    def study_properties_editor(self):
        return self._study_properties_editor

    def update_study(self):
        self._study_properties_editor.update_study(self.study)
        self._subjects_editor.update_study(self.study, \
                                self.study_update_policy)


class StudyEditorDialog(QtGui.QDialog):
    window_title_from_mode = [\
        "Create a new study",
        "Edit current study"]
    on_apply_cancel_buttons_clicked_map = {}
    default_group = Subject.DEFAULT_GROUP
    group_column_width = 100

    @classmethod
    def _init_class(cls):
        apply_role = QtGui.QDialogButtonBox.ApplyRole
        reject_role = QtGui.QDialogButtonBox.RejectRole
        role_map = cls.on_apply_cancel_buttons_clicked_map
        role_map[apply_role] = cls.on_apply_button_clicked
        role_map[reject_role] = cls.on_cancel_button_clicked

    def __init__(self, study, parent=None, editor_mode=StudyEditor.NEW_STUDY,
                        enable_brainomics_db=False):
        super(StudyEditorDialog, self).__init__(parent)
        self._init_ui()
        self.study_editor = StudyEditor(study, editor_mode)
        self._set_window_title(editor_mode)
        self._default_parameter_template = study.analysis_cls().PARAMETER_TEMPLATES[0]

        self._subjects_tablemodel = SubjectsEditorTableModel(\
                            self.study_editor.subjects_editor)
        self._subjects_tablemodel.rowsRemoved.connect(self.on_subjects_tablemodel_rows_changed)
        self._subjects_tablemodel.modelReset.connect(self.on_subjects_tablemodel_changed)
        self.ui.subjects_tableview.setModel(self._subjects_tablemodel)
        tablewidget_header = self.ui.subjects_tableview.horizontalHeader()
        tablewidget_header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self._selection_model = SubjectsEditorSelectionModel(\
                                    self._subjects_tablemodel)
        self.ui.subjects_tableview.setSelectionModel(self._selection_model)
        self._selection_model.selectionChanged.connect(self.on_subjects_selection_changed)

        self._study_properties_editor_widget = StudyPropertiesEditorWidget(\
                                    self.study_editor.study_properties_editor,
                                    self, editor_mode)

        self._study_properties_editor_widget.validity_changed.connect(self.on_study_properties_editor_validity_changed)

        self._init_subjects_from_study_dialog(study)
        self._init_db_dialog(enable_brainomics_db)

    def _init_ui(self):
        uifile = os.path.join(ui_directory, 'study_editor_widget.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)

    def _init_db_dialog(self, enable_brainomics_db):
        if enable_brainomics_db:
            self.ui.add_subjects_from_database_button.setEnabled(True)
            self._subject_from_db_dialog = SubjectsFromDatabaseDialog(self.ui)
            self._subject_from_db_dialog.set_group(self.default_group)
            self._subject_from_db_dialog.set_server_url("http://neurospin-cubicweb.intra.cea.fr:8080")
            self._subject_from_db_dialog.set_rql_request('''Any X WHERE X is Scan, X type "raw T1", X concerns A, A age 25''')
            self._subject_from_db_dialog.accepted.connect(self.on_subject_from_db_dialog_accepted)
        else:
            self.ui.add_subjects_from_database_button.hide()    
             
    def _init_subjects_from_study_dialog(self, study):
        outputdir = study.outputdir
        parameter_templates = study.analysis_cls().PARAMETER_TEMPLATES
        selected_template = self._default_parameter_template
        self._subjects_from_study_dialog = SelectStudyDirectoryDialog(self.ui,
                            outputdir, parameter_templates, selected_template)
        self._subjects_from_study_dialog.accepted.connect(\
            self.on_subjects_from_study_dialog_accepted)

    def _set_window_title(self, mode):
        self.setWindowTitle(self.window_title_from_mode[mode])
       
    @QtCore.Slot("const QModelIndex &", "int", "int")
    def on_subjects_tablemodel_rows_changed(self):
        self._on_table_model_changed()

    @QtCore.Slot()
    def on_subjects_tablemodel_changed(self):
        self._on_table_model_changed()

    def _on_table_model_changed(self):
        self._selection_model.reset()
        empty_item_selection = QtGui.QItemSelection()
        dummy_item_selection = QtGui.QItemSelection()
        self.on_subjects_selection_changed(empty_item_selection,
                                           dummy_item_selection)
                                          
    @QtCore.Slot("bool")
    def on_study_properties_editor_validity_changed(self, valid):
        self.ui.apply_button.setEnabled(valid)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_one_subject_from_a_file_button_clicked(self):
        dialog = SelectSubjectsDialog(self.ui)
        dialog.filesSelected.connect(self.on_select_subjects_dialog_files_selected)
        dialog.show()

    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_subjects_from_a_study_directory_button_clicked(self):
        self._subjects_from_study_dialog.show()
        
    # this slot is automagically connected
    @QtCore.Slot()
    def on_subjects_from_study_dialog_accepted(self):
        study_directory = self._subjects_from_study_dialog.get_study_directory()
        parameter_template_name = self._subjects_from_study_dialog.get_study_parameter_template()
        parameter_template = self.study_editor.study_properties_editor.analysis_cls.param_template_map[parameter_template_name]
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        subjects = parameter_template.get_subjects(study_directory)
        QtGui.QApplication.restoreOverrideCursor()
        if not subjects:
            QtGui.QMessageBox.warning(self, "No subjects", 
                                      "Cannot find subjects in this directory.")
        else:
            self._subjects_tablemodel.add_subjects(subjects)
 
    @QtCore.Slot("const QItemSelection &", "const QItemSelection &")
    def on_subjects_selection_changed(self, selected, deselected):
        enable_rename = self._selection_model.has_any_new_selected_subjects()
        enable_remove = bool(self._selection_model.selectedRows())
        self.ui.edit_subjects_name_button.setEnabled(enable_rename)
        self.ui.edit_subjects_group_button.setEnabled(enable_rename)
        self.ui.remove_subjects_button.setEnabled(enable_remove)
           
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_name_button_clicked(self):
        subjectname, ok = QtGui.QInputDialog.getText(self, 
                "Enter the subject name", "Subject name:")
        if not ok: return
        rows = [index.row() for index in \
                self._selection_model.new_selected_subjects_rows()]
        self._subjects_tablemodel.rename_subjects_name_from_rows(subjectname, rows)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_group_button_clicked(self): 
        groupname, ok = QtGui.QInputDialog.getText(self,
                "Enter the group name", "Group name:")
        if not ok: return
        rows = [index.row() for index in \
                self._selection_model.new_selected_subjects_rows()]
        self._subjects_tablemodel.rename_subjects_groupname_from_rows(groupname, rows)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_remove_subjects_button_clicked(self):
        range_list = []
        for selection_range in self._selection_model.selection():
            start_row = selection_range.top()
            count = selection_range.bottom() - start_row + 1
            range_list.append((start_row, count))
        self._subjects_tablemodel.remove_subjects_from_range_list(range_list)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_subjects_from_database_button_clicked(self):
        self._subject_from_db_dialog.show()
       
    @QtCore.Slot() 
    def on_subject_from_db_dialog_accepted(self):
        self._subjects_tablemodel.add_subjects_from_filenames(\
                            self._subject_from_db_dialog.get_filenames(), 
                            self._subject_from_db_dialog.get_group())

    # this slot is automagically connected
    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_buttons_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        self.on_apply_cancel_buttons_clicked_map[role](self)

    def on_apply_button_clicked(self):
        if not self._check_study_consistency():
            return

        if self.study_editor.subjects_editor.has_subjects_to_be_removed():
            title = 'Removed subjects from a study'
            msg = 'The following subjects will be removed from the current ' +\
                'study.\nDo you want to removed associated files?'
            msgbox = QtGui.QMessageBox(self)
            msgbox.setWindowTitle(title)
            msgbox.setText(msg)
            cancel_button = msgbox.addButton(QtGui.QMessageBox.Cancel)
            no_button = msgbox.addButton("Keep files", QtGui.QMessageBox.NoRole)
            yes_button = msgbox.addButton("Remove files", QtGui.QMessageBox.YesRole)
            msgbox.setIcon(QtGui.QMessageBox.Question)
            msgbox.exec_()
            answer = msgbox.clickedButton()
            if answer == yes_button:
                study_update_policy = StudyEditor.ON_SUBJECT_REMOVED_DELETE_FILES
            elif answer == no_button:
                study_update_policy = StudyEditor.ON_SUBJECT_REMOVED_DO_NOTHING
            elif answer == cancel_button:
                return
            else:
                assert(0)
            self.study_editor.study_update_policy = study_update_policy
        self.ui.accept()

    def on_cancel_button_clicked(self):
        self.ui.reject()

    @QtCore.Slot("const QStringList &")
    def on_select_subjects_dialog_files_selected(self, filenames):
        self._subjects_tablemodel.add_subjects_from_filenames(filenames,
                                                    self.default_group)

    def _check_study_consistency(self):
        study_properties_editor = self.study_editor.study_properties_editor
        subjects_editor = self.study_editor.subjects_editor
        outputdir = study_properties_editor.outputdir
        backup_filename = study_properties_editor.backup_filename
        backup_filename_directory = os.path.dirname(backup_filename)
        editor_mode = self.study_editor.mode
        status = study_properties_editor.get_consistency_status(editor_mode)
        if status == StudyPropertiesEditor.STUDY_PROPERTIES_VALID:
            if subjects_editor.are_some_subjects_duplicated():
                QtGui.QMessageBox.critical(self, "Study consistency error",
                    "Some subjects have the same identifier")
                return False
            return True
        elif status & StudyPropertiesEditor.OUTPUTDIR_NOT_EXISTS:
            msg = "The output directory '%s' does not exist." % outputdir
        elif status & StudyPropertiesEditor.OUTPUTDIR_NOT_EMPTY:
            msg = "The output directory '%s' is not empty." % outputdir
        elif status & StudyPropertiesEditor.BACKUP_FILENAME_DIR_NOT_EXISTS:
            msg = "The backup filename directory '%s' does not exist." % \
                                                backup_filename_directory
        elif status & StudyPropertiesEditor.BACKUP_FILENAME_EXISTS:
            msg = "The backup filename already '%s' exists." % backup_filename
        else:
            assert(0)
        QtGui.QMessageBox.critical(self, "Study consistency error", msg)
        return False


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
        for param_template_name in parameter_templates: 
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
 
    def submit(self):
        obj = self.sender()
        delegate = self.itemDelegate()
        model = self.model()
        if not model.isEdited():
            delegate.commitData.emit(obj)


class StudyPropertiesEditorItemDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(StudyPropertiesEditorItemDelegate, self).__init__(parent)
        
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
    PARAMETER_TEMPLATE_COL = 3
    attributes = ["name", "outputdir", "backup_filename", "parameter_template"]
    status_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_properties_editor, parent=None):
        super(StudyPropertiesEditorItemModel, self).__init__(parent)
        self._study_properties_editor = study_properties_editor
        self.linked_inputs = True # model for the link button
        self._is_edited = False
        self._status = True # ok si 3 first attributes != ''

    def columnCount(self):
        return 4

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 1

    def index(self, row, column, parent=QtCore.QModelIndex()):
        return self.createIndex(row, column, self)

    def parent(self, index=QtCore.QModelIndex()):
        return QtCore.QModelIndex()

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

    def is_data_colorable(self, index):
        column = index.column()
        return column in [self.NAME_COL, self.OUTPUTDIR_COL,
                                    self.BACKUP_FILENAME_COL]

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

    def set_data(self, col, value):
        row = 0
        index = self.index(row, col)
        return self.setData(index, value)

    def _invalid_value(self, value):
        return value == ''

    def isEdited(self):
        return self._is_edited


class StudyPropertiesEditor(object):
    # check status to build a study
    STUDY_PROPERTIES_VALID = 0x0
    OUTPUTDIR_NOT_EXISTS = 0x1
    OUTPUTDIR_NOT_EMPTY = 0x2
    BACKUP_FILENAME_DIR_NOT_EXISTS = 0x4
    BACKUP_FILENAME_EXISTS = 0x8
    
    def __init__(self, study):
        self.name = study.name
        self.outputdir = study.outputdir
        self.backup_filename = study.backup_filename 
        self.parameter_template = study.parameter_template
        # FIXME: store analysis name rather than class ?
        self._analysis_cls = study.analysis_cls()

    @property
    def analysis_cls(self):
        return self._analysis_cls

    def update_study(self, study):
        study.name = self.name
        study.outputdir = self.outputdir
        study.backup_filename = self.backup_filename 
        study.parameter_template = self.parameter_template

    def get_consistency_status(self, editor_mode):
        if editor_mode == StudyEditor.NEW_STUDY:
            status = self._outputdir_consistency_status()
            status |= self._backup_filename_consistency_status()
        elif editor_mode == StudyEditor.EDIT_STUDY:
            status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        return status

    def _outputdir_consistency_status(self):
        status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        if not os.path.exists(self.outputdir):
            status |= StudyPropertiesEditor.OUTPUTDIR_NOT_EXISTS
        elif len(os.listdir(self.outputdir)) != 0:
            status |= StudyPropertiesEditor.OUTPUTDIR_NOT_EMPTY
        return status
            
    def _backup_filename_consistency_status(self):
        status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        backup_filename_directory = os.path.dirname(self.backup_filename)
        if not os.path.exists(backup_filename_directory):
            status |= StudyPropertiesEditor.BACKUP_FILENAME_DIR_NOT_EXISTS
        elif os.path.exists(self.backup_filename):
            status |= StudyPropertiesEditor.BACKUP_FILENAME_EXISTS
        return status


class SubjectsEditorSelectionModel(QtGui.QItemSelectionModel):

    def __init__(self, model, parent=None):
        super(SubjectsEditorSelectionModel, self).__init__(model, parent)

    def new_selected_subjects_rows(self, column=0):
        model = self.model()
        model_index_list = [index for index in self.selectedRows(column) \
                                if model.is_ith_subject_new(index.row())]
        return model_index_list

    def has_any_new_selected_subjects(self, column=0):
        model = self.model()
        for index in self.selectedRows(column):
            if model.is_ith_subject_new(index.row()):
                return True
        return False


class SubjectsEditorTableModel(QtCore.QAbstractTableModel):
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2
    header = ['Group', 'Name', 'Filename']

    def __init__(self, subjects_editor, parent=None):
        super(SubjectsEditorTableModel, self).__init__(parent)
        self._subjects_editor = subjects_editor
        self.reset()

    # QT methods
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._subjects_editor)

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
            subject = self._subjects_editor[row]
            if column == self.GROUPNAME_COL:
                return subject.groupname
            elif column == self.SUBJECTNAME_COL:
                return subject.name
            elif column == self.FILENAME_COL:
                return subject.filename
        elif role == QtCore.Qt.BackgroundRole:
            if self._subjects_editor.is_ith_subject_duplicated(row):
                return QtGui.QColor("#ffaaaa")
        elif role == QtCore.Qt.ForegroundRole:
            if not self._subjects_editor.is_ith_subject_new(row):
                return QtGui.QApplication.palette().color(\
                    QtGui.QPalette.Disabled, QtGui.QPalette.Text)

    def removeRows(self, start_row, count, parent=QtCore.QModelIndex()):
        end_row = start_row + count - 1
        self.beginRemoveRows(parent, start_row, end_row)
        # remove rows from bottom to top to avoid changing the rows indexes
        for row in range(end_row, start_row - 1, -1):
            del self._subjects_editor[row]
        self.endRemoveRows()

    # additional methods
    def add_subjects_from_filenames(self, filenames, groupname):
        parent = QtCore.QModelIndex()
        start_index = self.rowCount()
        end_index = start_index + len(filenames)
        self.beginInsertRows(parent, start_index, end_index)
        for filename in filenames:
            subject = Subject.from_filename(filename, groupname)
            self._add_subject(subject)
        self.endInsertRows()

    def add_subjects(self, subjects):
        parent = QtCore.QModelIndex()
        start_index = self.rowCount()
        end_index = start_index + len(subjects)
        self.beginInsertRows(parent, start_index, end_index)
        for subject in subjects:
            self._add_subject(subject)
        self.endInsertRows()

    def _add_subject(self, subject):
        self._subjects_editor.append(subject)

    def rename_subjects_name_from_rows(self, subjectname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_editor.update_ith_subject_property(row,
                                                        "name", subjectname)
        start_index = self.index(start_row, self.SUBJECTNAME_COL)
        end_index = self.index(end_row, self.SUBJECTNAME_COL)
        self.dataChanged.emit(start_index, end_index)

    def is_ith_subject_new(self, row):
        return self._subjects_editor.is_ith_subject_new(row)
    
    def rename_subjects_groupname_from_rows(self, groupname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_editor.update_ith_subject_property(row,
                                                    "groupname", groupname)
        start_index = self.index(start_row, self.GROUPNAME_COL)
        end_index = self.index(end_row, self.GROUPNAME_COL)
        self.dataChanged.emit(start_index, end_index)

    def remove_subjects_from_range_list(self, range_list):
        # remove rows from bottom to top to avoid changing the rows indexes
        range_list.sort(reverse=True)
        for start_row, count in range_list:
            self.removeRows(start_row, count)


class SubjectsEditor(object):
    IdentifiedSubject = namedtuple('SubjectOrigin', ['id', 'subject'])
   
    def __init__(self, study):
        self._subjects_origin = []
        self._subjects = []
        self._removed_subjects_id = []
        self._similar_subjects_n = {}
        # FIXME: store this information in ImportationError
        self._has_imported_some_subjects = False
        for subject_id, subject in study.subjects.iteritems():
            subject_copy = subject.copy()
            self._subjects.append(subject_copy)
            origin = self.IdentifiedSubject(subject_id, subject)
            self._subjects_origin.append(origin)
            self._similar_subjects_n.setdefault(subject_id, 0)
            self._similar_subjects_n[subject_id] += 1

    def __len__(self):
        return len(self._subjects)

    def __getitem__(self, index): 
        return self._subjects[index]

    def __delitem__(self, index): 
        subject = self._subjects[index]
        subject_id = subject.id()
        self._similar_subjects_n[subject_id] -= 1
        if self._similar_subjects_n[subject_id] == 0:
            del self._similar_subjects_n[subject_id]
        origin = self._subjects_origin[index]
        if origin is not None:
            self._removed_subjects_id.append(origin.id)
        del self._subjects_origin[index]
        del self._subjects[index]

    def __iter__(self):
        for subject in self._subjects:
            yield subject

    def append(self, subject):
        self._subjects.append(subject)
        self._subjects_origin.append(None)
        subject_id = subject.id()
        self._similar_subjects_n.setdefault(subject_id, 0)
        self._similar_subjects_n[subject_id] += 1

    def is_ith_subject_duplicated(self, index):
        subject = self._subjects[index]
        subject_id = subject.id()
        return self._similar_subjects_n[subject_id] != 1

    def is_ith_subject_new(self, index):
        return self._subjects_origin[index] is None

    def update_ith_subject_property(self, index, property, value):
        subject = self._subjects[index] 
        old_subject_id = subject.id()
        subject.__setattr__(property, value)
        new_subject_id = subject.id()
        self._similar_subjects_n[old_subject_id] -= 1
        if self._similar_subjects_n[old_subject_id] == 0:
            del self._similar_subjects_n[old_subject_id]
        self._similar_subjects_n.setdefault(new_subject_id, 0)
        self._similar_subjects_n[new_subject_id] += 1

    def update_study(self, study, study_update_policy):
        # XXX: operations order is important : del, rename, add
        for subject_id in self._removed_subjects_id:
            self._removed_subjects_from_study(study,
                        subject_id, study_update_policy)

        if len(self._renamed_subjects()):
            assert(0) # existing subjects can't be renamed from GUI
 
        subjects_importation_failed = []
        for subject in self._added_subjects():
            try:
                study.add_subject(subject)
            except ImportationError, e:
                subjects_importation_failed.append(subject)
            else:
                self._has_imported_some_subjects = True
        if subjects_importation_failed:
            str_subjects = []
            for subject in subjects_importation_failed:
                str_subjects.append(str(subject))
            raise ImportationError("The importation failed for the " + \
                "following subjects:\n%s." % ", ".join(str_subjects))

    def _added_subjects(self):
        added_subjects = []
        for index, _ in enumerate(self):
            subject = self._subjects[index]
            origin = self._subjects_origin[index]
            if origin is None:
                added_subjects.append(subject)
        return added_subjects

    def _renamed_subjects(self):
        renamed_subjects = []
        for index, _ in enumerate(self):
            subject = self._subjects[index]
            origin = self._subjects_origin[index]
            if origin is None: continue
            if subject != origin.subject:
                renamed_subjects.append((origin, subject))
        return renamed_subjects

    def has_subjects_to_be_removed(self):
        return len(self._removed_subjects_id)

    # FIXME: store this information in ImportationError
    def has_imported_some_subjects(self):
        return self._has_imported_some_subjects

    def _removed_subjects_from_study(self, study, subject_id,
                                        study_update_policy):
        if study_update_policy == StudyEditor.ON_SUBJECT_REMOVED_DELETE_FILES:
            study.remove_subject_and_files_from_id(subject_id)
        elif study_update_policy == StudyEditor.ON_SUBJECT_REMOVED_DO_NOTHING:
            study.remove_subject_from_id(subject_id)
        else:
            assert(0)

    def are_some_subjects_duplicated(self):
        for n in self._similar_subjects_n.values():
            if n != 1: return True
        return False


class SelectSubjectsDialog(QtGui.QFileDialog):
    
    def __init__(self, parent):
        caption = "Select one or more subjects to be included into your study"
        files_filter = self._define_selectable_files_regexp()
        default_directory = ""
        super(SelectSubjectsDialog, self).__init__(parent, caption,
                                    default_directory, files_filter)
        self.setObjectName("SelectSubjectsDialog")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setFileMode(QtGui.QFileDialog.ExistingFiles)

    def _define_selectable_files_regexp(self):
        formats_manager = FormatsManager.formats_manager()
        formats = formats_manager.formats()

        volume_filters = []
        all_volumes_regexp = []
        for format in formats:
            extensions = format.extensions
            extensions_regexp = (' '.join([('*.' + ext) for ext in extensions]))
            if extensions_regexp == '': continue
            filter = '%s (%s)' % (format.name, extensions_regexp)
            volume_filters.append(filter)
            all_volumes_regexp.append(extensions_regexp)
        all_volumes_filter = '3D Volumes (%s)' % (' '.join(all_volumes_regexp))
        all_filters = [all_volumes_filter] + volume_filters +['All files (*.*)']
        final_filter = ';;'.join(all_filters)
        return final_filter


class SelectStudyDirectoryDialog(QtGui.QDialog):
    
    def __init__(self, parent, default_study_directory, 
                 parameter_templates, selected_template):
        super(SelectStudyDirectoryDialog, self).__init__(parent)
        
        uifile = os.path.join(ui_directory, 'select_study_directory.ui')
        self.ui = loadUi(uifile, self)
        
        self.ui.study_directory_lineEdit.setText(default_study_directory)
        
        for param_template_name in parameter_templates:
            self.ui.parameter_template_combobox.addItem(param_template_name)
            if param_template_name == selected_template:
                self.ui.parameter_template_combobox.setCurrentIndex(self.ui.parameter_template_combobox.count()-1)
    
    def get_study_directory(self):
        return self.ui.study_directory_lineEdit.text()
    
    def get_study_parameter_template(self):
        return self.ui.parameter_template_combobox.currentText()

    # this slot is automagically connected
    @QtCore.Slot()
    def on_study_directory_button_clicked(self):
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                caption="Select a study directory", 
                                directory=self.get_study_directory(), 
                                options=QtGui.QFileDialog.DontUseNativeDialog)
        if selected_directory != '':
            self.ui.study_directory_lineEdit.setText(selected_directory)


class SubjectsFromDatabaseDialog(QtGui.QDialog):

    def __init__(self, parent):
        super(SubjectsFromDatabaseDialog, self).__init__(parent)

        uifile = os.path.join(ui_directory, 'rql_subjects_widget.ui')
        self.ui = loadUi(uifile, self)
        
        self._filenames = []
        self._groupname = None
   
        tmp_directory = tempfile.gettempdir()
        self._zip_filename = os.path.join(tmp_directory, "cubic_web_tmp_data.zip")
        self._unzipped_dirname = os.path.join(tmp_directory, "cubic_web_unzipped_dir")
        self._files_directory = os.path.join(tmp_directory, "morphologist_tmp_files")
        if os.path.isdir(self._files_directory):
            shutil.rmtree(self._files_directory)
        os.mkdir(self._files_directory)

    # this slot is automagically connected 
    @QtCore.Slot()
    def on_load_button_clicked(self):
        self.ui.load_button.setEnabled(False)
        QtGui.QApplication.processEvents()
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        error = None
        try:
            self.load(self.ui.server_url_field.text(), 
                      self.ui.rql_request_lineEdit.text())
        except LoadSubjectsFromDatabaseError, e:
            error = "Cannot load files from the database: \n%s" % unicode(e)
        finally:
            QtGui.QApplication.restoreOverrideCursor()
            self.ui.load_button.setEnabled(True)
        self._group = self.ui.group_lineEdit.text()
        if error:
            QtGui.QMessageBox.critical(self, "Load error", error)
        else:
            self.accept()

    def set_server_url(self, server_url):
        self.ui.server_url_field.setText(server_url)

    def set_rql_request(self, rql_request):
        self.ui.rql_request_lineEdit.setText(rql_request)

    def set_group(self, groupname):
        self.ui.group_lineEdit.setText(groupname)

    def get_filenames(self):
        return self._filenames
    
    def get_group(self):
        return self._group

    def load(self, server_url, rql_request):
        url = server_url + '''/view?rql=''' + rql_request + '''&vid=data-zip'''
        try:
            urllib.urlretrieve(url, self._zip_filename)
        except IOError:
            raise LoadSubjectsFromDatabaseError("Cannot connect to the database server.")

        try:
            zip_file = zipfile.ZipFile(self._zip_filename)
            zip_file.extractall(self._unzipped_dirname)
        except zipfile.BadZipfile:
            raise LoadSubjectsFromDatabaseError("The request is incorrect or has no results.")
        
        self._filenames = []
        dirname = os.path.join(self._unzipped_dirname, "brainomics_data")
        subject_dirs = os.listdir(dirname)
        for subject_name in subject_dirs:
            filename = os.path.join(self._files_directory, subject_name + ".nii.gz")
            shutil.move(os.path.join(dirname, subject_name, "raw_T1_raw_anat.nii.gz"), filename)
            self._filenames.append(filename)
    
        if os.path.isdir(self._unzipped_dirname):
            shutil.rmtree(self._unzipped_dirname)
 

class LoadSubjectsFromDatabaseError(Exception):
    pass        


StudyEditorDialog._init_class()
