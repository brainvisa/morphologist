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


# XXX: issue: subject.id() is used to compare subjects
class SubjectsEditorModel(object):
    
    def __init__(self, study):
        self._subjects_origin = []
        self._subjects = []
        # FIXME: find a better name
        self._similar_subjects_n = {}
        for subject_id, subject in study.subjects.iteritems():
            subject_copy = subject.copy()
            self._subjects.append(subject_copy)
            self._subjects_origin.append(subject)
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
        # TODO : register deleted subjects if origin is not None
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
        return self._subjects_origin[index] is not None

    def rename_ith_subject_name(self, row, name):
        subject = self._subjects[row] 
        self._update_subject_field(subject, "name", name)

    def rename_ith_subject_groupname(self, row, name):
        subject = self._subjects[row] 
        self._update_subject_field(subject, "groupname", name)

    def _update_subject_field(self, subject, attrib, value):
        old_subject_id = subject.id()
        subject.__setattr__(attrib, value)
        new_subject_id = subject.id()
        self._similar_subjects_n[old_subject_id] -= 1
        if self._similar_subjects_n[old_subject_id] == 0:
            del self._similar_subjects_n[old_subject_id]
        self._similar_subjects_n.setdefault(new_subject_id, 0)
        self._similar_subjects_n[new_subject_id] += 1

    # FIXME: find a better name ?
    def check_study_consistency(self):
        return self._is_some_subjects_duplicated()

    def _is_some_subjects_duplicated(self):
        for n in self._similar_subjects_n.values():
            if n != 1: return True
        return False

 
# TODO: rename ?
class SubjectsEditorTableModel(QtCore.QAbstractTableModel):
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2
    header = ['Group', 'Name', 'Filename']

    def __init__(self, subjects_editor_model, parent=None):
        super(SubjectsEditorTableModel, self).__init__(parent)
        self._subjects_editor_model = subjects_editor_model
        self.reset()

    # QT methods
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._subjects_editor_model)

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
            subject = self._subjects_editor_model[row]
            if column == self.GROUPNAME_COL:
                return subject.groupname
            elif column == self.SUBJECTNAME_COL:
                return subject.name
            elif column == self.FILENAME_COL:
                return subject.filename
        elif role == QtCore.Qt.BackgroundRole:
            if self._subjects_editor_model.is_ith_subject_duplicated(row):
                return QtGui.QColor("#ffaaaa")
            elif self._subjects_editor_model.is_ith_subject_new(row):
                return QtGui.QColor("#ccccff")

    def removeRows(self, start_row, count, parent=QtCore.QModelIndex()):
        end_row = start_row + count - 1
        self.beginRemoveRows(parent, start_row, end_row)
        # remove rows from bottom to top to avoid changing the rows indexes
        for row in range(end_row, start_row - 1, -1):
            del self._subjects_editor_model[row]
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
        self._subjects_editor_model.append(subject)

    def rename_subjects_name_from_rows(self, subjectname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_editor_model.rename_ith_subject_name(row,
                                                        subjectname)
        start_index = self.index(start_row, self.SUBJECTNAME_COL)
        end_index = self.index(end_row, self.SUBJECTNAME_COL)
        self.dataChanged.emit(start_index, end_index)
    
    def rename_subjects_groupname_from_rows(self, groupname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_editor_model.rename_ith_subject_groupname(row,
                                                        groupname)
        start_index = self.index(start_row, self.GROUPNAME_COL)
        end_index = self.index(end_row, self.GROUPNAME_COL)
        self.dataChanged.emit(start_index, end_index)

    def remove_subjects_from_range_list(self, range_list):
        # remove rows from bottom to top to avoid changing the rows indexes
        range_list.sort(reverse=True)
        for start_row, count in range_list:
            self.removeRows(start_row, count)


class StudyConfig(object):
    # check status to build a study
    STUDY_CONFIG_VALID = 0x0
    OUTPUTDIR_NOT_EXISTS = 0x1
    OUTPUTDIR_NOT_EMPTY = 0x2
    BACKUP_FILENAME_DIR_NOT_EXISTS = 0x4
    BACKUP_FILENAME_EXISTS = 0x8
    
    def __init__(self, study):
        self.name = study.name
        self.outputdir = study.outputdir
        self.backup_filename = study.backup_filename 
        self.parameter_template = study.analysis_cls().PARAMETER_TEMPLATES[0]

    # FIXME: find a better name ?
    def check_study_consistency(self):
        status = self._check_valid_outputdir()
        status |= self._check_valid_backup_filename()
        return status

    def _check_valid_outputdir(self):
        status = StudyConfig.STUDY_CONFIG_VALID
        if not os.path.exists(self.outputdir):
            status |= StudyConfig.OUTPUTDIR_NOT_EXISTS
        elif len(os.listdir(self.outputdir)) != 0:
            status |= StudyConfig.OUTPUTDIR_NOT_EMPTY
        return status
            
    def _check_valid_backup_filename(self):
        status = StudyConfig.STUDY_CONFIG_VALID
        backup_filename_directory = os.path.dirname(self.backup_filename)
        if not os.path.exists(backup_filename_directory):
            status |= StudyConfig.BACKUP_FILENAME_DIR_NOT_EXISTS
        elif os.path.exists(self.backup_filename):
            status |= StudyConfig.BACKUP_FILENAME_EXISTS
        return status


class StudyConfigItemModel(QtCore.QAbstractItemModel):
    NAME_COL = 0
    OUTPUTDIR_COL = 1
    BACKUP_FILENAME_COL = 2
    PARAMETER_TEMPLATE_COL = 3
    attributes = ["name", "outputdir", "backup_filename", "parameter_template"]
    status_changed = QtCore.pyqtSignal(bool)

    def __init__(self, study_config, parent=None):
        super(StudyConfigItemModel, self).__init__(parent)
        self._study_config = study_config
        self.linked_inputs = True
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
        value = self._study_config.__getattribute__(self.attributes[column])
        if role in [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole]:
            return value
        elif role == QtCore.Qt.BackgroundRole:
            if column in [self.NAME_COL, self.OUTPUTDIR_COL,
                                self.BACKUP_FILENAME_COL]:
                if self._invalid_value(value):
                    return QtGui.QColor('#ffaaaa')
                else:
                    return QtGui.QColor('white')

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        self._is_edited = True
        column = index.column() 
        attribute = self.attributes[column]
        old_status = self._status
        if role != QtCore.Qt.EditRole: return
        self._study_config.__setattr__(attribute, value)
        self.dataChanged.emit(index, index)
        if self.linked_inputs:
            if column == self.OUTPUTDIR_COL:
                backup_filename = Study.default_backup_filename_from_outputdir(value)
                column_to_be_updated = self.BACKUP_FILENAME_COL
                attrib = self.attributes[column_to_be_updated]
                self._study_config.__setattr__(attrib, backup_filename)
                changed_index = self.index(index.row(), column_to_be_updated)
                self.dataChanged.emit(changed_index, changed_index)
            elif column == self.BACKUP_FILENAME_COL:
                outputdir = Study.default_outputdir_from_backup_filename(value)
                column_to_be_updated = self.OUTPUTDIR_COL
                attrib = self.attributes[column_to_be_updated]
                self._study_config.__setattr__(attrib, outputdir)
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


class StudyConfigWidgetMapper(QtGui.QDataWidgetMapper):

    def __init__(self, parent=None):
        super(StudyConfigWidgetMapper, self).__init__(parent)
 
    def submit(self):
        obj = self.sender()
        delegate = self.itemDelegate()
        model = self.model()
        if not model.isEdited():
            delegate.commitData.emit(obj)
 

class StudyConfigItemDelegate(QtGui.QItemDelegate):

    def __init__(self, parent=None):
        super(StudyConfigItemDelegate, self).__init__(parent)
        
    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, QtCore.Qt.EditRole)
        property = editor.metaObject().userProperty().name()
        # don't update editor if not needed: fix cursor issue
        if value != editor.property(property):
            editor.setProperty(property, value)
        color = model.data(index, QtCore.Qt.BackgroundRole)
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
    ''' % tuple([color.name()] * 2)
        editor.setStyleSheet(style_sheet)


class StudyEditorDialog(QtGui.QDialog):
    NEW_STUDY = 0
    EDIT_STUDY = 1
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

    def __init__(self, study, parent=None, mode=NEW_STUDY,
                        enable_brainomics_db=False):
        super(StudyEditorDialog, self).__init__(parent)
        self.study = study # FIXME : remove this line
        self._dialog_mode = mode
        self._subjects_editor_model = SubjectsEditorModel(study)
        self._tablemodel = SubjectsEditorTableModel(self._subjects_editor_model)
        
        self.parameter_template = None
        self._default_parameter_template = study.analysis_cls().PARAMETER_TEMPLATES[0]
        uifile = os.path.join(ui_directory, 'study_editor_widget.ui')
        self.ui = loadUi(uifile, self)

        self._study_config = StudyConfig(study)
        self._study_config_item_model = StudyConfigItemModel(self._study_config, self)
        self._study_config_item_delegate = StudyConfigItemDelegate(self)
        mapper = StudyConfigWidgetMapper(self)
        # XXX: AutoSubmit used else commitData is not listened by mapper
        mapper.setSubmitPolicy(QtGui.QDataWidgetMapper.AutoSubmit)
        mapper.setModel(self._study_config_item_model)        
        mapper.setItemDelegate(self._study_config_item_delegate)
        mapper.addMapping(self.ui.studyname_lineEdit, 0)
        mapper.addMapping(self.ui.outputdir_lineEdit, 1)
        mapper.addMapping(self.ui.backup_filename_lineEdit, 2)
        self.ui.studyname_lineEdit.textChanged.connect(mapper.submit)
        self.ui.outputdir_lineEdit.textChanged.connect(mapper.submit)
        self.ui.backup_filename_lineEdit.textChanged.connect(mapper.submit)
        self.mapper = mapper
        mapper.toFirst()

        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)


        self._create_parameter_template_combobox(study)
        self.ui.subjects_tableview.setModel(self._tablemodel)
        tablewidget_header = self.ui.subjects_tableview.horizontalHeader()
        tablewidget_header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self._selection_model = self.ui.subjects_tableview.selectionModel()
        self._selection_model.selectionChanged.connect(self.on_subjects_selection_changed)
        self._tablemodel.rowsRemoved.connect(self.on_tablemodel_rows_changed)
        self._tablemodel.modelReset.connect(self.on_tablemodel_changed)

        self._study_config_item_model.status_changed.connect(self.on_study_config_item_status_changed)

        if mode == StudyEditorDialog.EDIT_STUDY:
            self.ui.outputdir_lineEdit.setEnabled(False)
            self.ui.outputdir_button.setEnabled(False)
            self.ui.backup_filename_lineEdit.setEnabled(False)
            self.ui.backup_filename_button.setEnabled(False)
            self.ui.link_button.setEnabled(False)
            self.ui.parameter_template_combobox.setEnabled(False)
        
        self._init_subjects_from_study_dialog(study)
        self._init_db_dialog(enable_brainomics_db)
       
    @QtCore.Slot("const QModelIndex &", "int", "int")
    def on_tablemodel_rows_changed(self):
        self._on_table_model_changed()

    @QtCore.Slot()
    def on_tablemodel_changed(self):
        self._on_table_model_changed()

    def _on_table_model_changed(self):
        self._selection_model.reset()
        empty_item_selection = QtGui.QItemSelection()
        dummy_item_selection = QtGui.QItemSelection()
        self.on_subjects_selection_changed(empty_item_selection,
                                           dummy_item_selection)

    def _create_parameter_template_combobox(self, study):
        for param_template_name in study.analysis_cls().PARAMETER_TEMPLATES:
            self.ui.parameter_template_combobox.addItem(param_template_name)
            if param_template_name == self._default_parameter_template:
                self.ui.parameter_template_combobox.setCurrentIndex(self.ui.parameter_template_combobox.count() - 1)

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

     # this slot is automagically connected
    @QtCore.Slot("bool")
    def on_link_button_toggled(self, checked):
        self._study_config_item_model.linked_inputs = (not checked)
                                                    
    @QtCore.Slot("bool")
    def on_study_config_item_status_changed(self, valid):
        self.ui.apply_button.setEnabled(valid)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_outputdir_button_clicked(self):
        caption = 'Select study output directory'
        default_directory = self._study_config.outputdir
        if default_directory == '':
            default_directory = os.getcwd()
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                                caption, default_directory) 
        if selected_directory != '':
            self._study_config_item_model.set_data(\
                StudyConfigItemModel.OUTPUTDIR_COL, selected_directory)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_backup_filename_button_clicked(self):
        caption = 'Select study backup filename'
        default_filename = self._study_config.backup_filename
        if default_filename == '':
            default_filename = os.path.join(os.getcwd(), 'study.json')
        selected_filename = QtGui.QFileDialog.getSaveFileName(self.ui,
                                                caption, default_filename) 
        if selected_filename != '':
            self._study_config_item_model.set_data(\
                StudyConfigItemModel.BACKUP_FILENAME_COL, selected_filename)

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
        parameter_template = self.study.analysis_cls().param_template_map[parameter_template_name]
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        subjects = parameter_template.get_subjects(study_directory)
        QtGui.QApplication.restoreOverrideCursor()
        if not subjects:
            QtGui.QMessageBox.warning(self, "No subjects", 
                                      "Cannot find subjects in this directory.")
        else:
            self._tablemodel.add_subjects(subjects)
 
    @QtCore.Slot("const QItemSelection &", "const QItemSelection &")
    def on_subjects_selection_changed(self, selected, deselected):
        enable = False
        if len(self._selection_model.selectedRows()):
            enable=True
        self.ui.edit_subjects_name_button.setEnabled(enable)
        self.ui.edit_subjects_group_button.setEnabled(enable)
        self.ui.remove_subjects_button.setEnabled(enable)
           
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_name_button_clicked(self):
        subjectname, ok = QtGui.QInputDialog.getText(self, 
                "Enter the subject name", "Subject name:")
        if not ok: return
        rows = [index.row() for index in self._selection_model.selectedRows()]
        self._tablemodel.rename_subjects_name_from_rows(subjectname, rows)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_group_button_clicked(self): 
        groupname, ok = QtGui.QInputDialog.getText(self,
                "Enter the group name", "Group name:")
        if not ok: return
        rows = [index.row() for index in self._selection_model.selectedRows()]
        self._tablemodel.rename_subjects_groupname_from_rows(groupname, rows)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_remove_subjects_button_clicked(self):
        range_list = []
        for selection_range in self._selection_model.selection():
            start_row = selection_range.top()
            count = selection_range.bottom() - start_row + 1
            range_list.append((start_row, count))
        self._tablemodel.remove_subjects_from_range_list(range_list)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_subjects_from_database_button_clicked(self):
        self._subject_from_db_dialog.show()
       
    @QtCore.Slot() 
    def on_subject_from_db_dialog_accepted(self):
        self._tablemodel.add_subjects_from_filenames(\
                            self._subject_from_db_dialog.get_filenames(), 
                            self._subject_from_db_dialog.get_group())

    # this slot is automagically connected
    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_buttons_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        self.on_apply_cancel_buttons_clicked_map[role](self)

    def on_apply_button_clicked(self):
        studyname = self._study_config.name
        outputdir = self._study_config.outputdir
        backup_filename = self._study_config.backup_filename
            
        # FIXME : remove study assignments
        if self._check_study_consistency(): 
            self.study.name = studyname
            self.study.outputdir = outputdir
            self.study.backup_filename = backup_filename 
            # TODO : update list of subject
            for subject in self._subjects_editor_model:
                self.study.add_subject(subject)
            self.parameter_template = self.ui.parameter_template_combobox.currentText()
            self.ui.accept()

    def on_cancel_button_clicked(self):
        self.ui.reject()

    @QtCore.Slot("const QStringList &")
    def on_select_subjects_dialog_files_selected(self, filenames):
        self._tablemodel.add_subjects_from_filenames(filenames,
                                                    self.default_group)

    def _check_study_consistency(self):
        outputdir = self._study_config.outputdir
        backup_filename = self._study_config.backup_filename
        backup_filename_directory = os.path.dirname(backup_filename)
        status = self._study_config.check_study_consistency()
        if status == StudyConfig.STUDY_CONFIG_VALID:
            if self._subjects_editor_model.check_study_consistency():
                QtGui.QMessageBox.critical(self, "Study consistency error",
                    "Some subjects have the same identifier")
                return False
            return True
        elif status & StudyConfig.OUTPUTDIR_NOT_EXISTS:
            msg = "The output directory '%s' does not exist." % outputdir
        elif status & StudyConfig.OUTPUTDIR_NOT_EMPTY:
            msg = "The output directory '%s' is not empty." % outputdir
        elif status & StudyConfig.BACKUP_FILENAME_DIR_NOT_EXISTS:
            msg = "The backup filename directory '%s' does not exist." % \
                                                backup_filename_directory
        elif status & StudyConfig.BACKUP_FILENAME_EXISTS:
            msg = "The backup filename already '%s' exists." % backup_filename
        else:
            assert(0)
        QtGui.QMessageBox.critical(self, "Study consistency error", msg)
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
