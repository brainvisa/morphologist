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
class SubjectsList(object):
    
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

    def is_some_subjects_duplicated(self):
        for n in self._similar_subjects_n.values():
            if n != 1: return True
        return False

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

 
class StudyTableModel(QtCore.QAbstractTableModel):
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2
    header = ['Group', 'Name', 'Filename']

    def __init__(self, subjects_list, parent=None):
        super(StudyTableModel, self).__init__(parent)
        self._subjects_list = subjects_list
        self.reset()

    # QT methods
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._subjects_list)

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
            subject = self._subjects_list[row]
            if column == self.GROUPNAME_COL:
                return subject.groupname
            elif column == self.SUBJECTNAME_COL:
                return subject.name
            elif column == self.FILENAME_COL:
                return subject.filename
        elif role == QtCore.Qt.BackgroundRole:
            if self._subjects_list.is_ith_subject_duplicated(row):
                return QtGui.QColor("#ffaaaa")
            elif self._subjects_list.is_ith_subject_new(row):
                return QtGui.QColor("#ccccff")

    def removeRows(self, start_row, count, parent=QtCore.QModelIndex()):
        end_row = start_row + count - 1
        self.beginRemoveRows(parent, start_row, end_row)
        # remove rows from bottom to top to avoid changing the rows indexes
        for row in range(end_row, start_row - 1, -1):
            del self._subjects_list[row]
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
        self._subjects_list.append(subject)

    def rename_subjects_name_from_rows(self, subjectname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_list.rename_ith_subject_name(row,
                                                        subjectname)
        start_index = self.index(start_row, self.SUBJECTNAME_COL)
        end_index = self.index(end_row, self.SUBJECTNAME_COL)
        self.dataChanged.emit(start_index, end_index)
    
    def rename_subjects_groupname_from_rows(self, groupname, rows):
        start_row = numpy.min(rows)
        end_row = numpy.min(rows)
        for row in rows:
            subject = self._subjects_list.rename_ith_subject_groupname(row,
                                                        groupname)
        start_index = self.index(start_row, self.GROUPNAME_COL)
        end_index = self.index(end_row, self.GROUPNAME_COL)
        self.dataChanged.emit(start_index, end_index)

    def remove_subjects_from_range_list(self, range_list):
        # remove rows from bottom to top to avoid changing the rows indexes
        range_list.sort(reverse=True)
        for start_row, count in range_list:
            self.removeRows(start_row, count)


class StudyEditorDialog(QtGui.QDialog):
    NEW_STUDY = 0
    EDIT_STUDY = 1
    on_apply_cancel_buttons_clicked_map = {}
    default_group = Subject.DEFAULT_GROUP
    group_column_width = 100
    lineEdit_style_sheet = '''
        QLineEdit {
            background-color: %s;
            border: 1px solid %s;
            border-radius: 4px;
            padding: 2px;
            margin: 1px;
        }
        QLineEdit:focus {
            background-color: %s;
            border: 1px solid %s;
            border-radius: 4px;
            padding: 2px;
            margin: 1px;
        }
    '''
    default_style_sheet = lineEdit_style_sheet % ('white', 'grey',
                                                  'white', '#ff7777')
    error_style_sheet = lineEdit_style_sheet % ('#ffaaaa', 'grey',
                                                '#ffaaaa', '#ff7777')

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
        self._subjects_list = SubjectsList(study)
        self._tablemodel = StudyTableModel(self._subjects_list)
        self.parameter_template = None
        self._default_parameter_template = study.analysis_cls().PARAMETER_TEMPLATES[0]
        self._lineEdit_lock = False
        uifile = os.path.join(ui_directory, 'study_editor_widget.ui')
        self.ui = loadUi(uifile, self)
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

        if mode == StudyEditorDialog.EDIT_STUDY:
            self.ui.outputdir_lineEdit.setEnabled(False)
            self.ui.outputdir_button.setEnabled(False)
            self.ui.backup_filename_lineEdit.setEnabled(False)
            self.ui.backup_filename_button.setEnabled(False)
            self.ui.link_button.setEnabled(False)
            self.ui.parameter_template_combobox.setEnabled(False)
        
        self._init_ui_from_study(study)
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

    def _init_ui_from_study(self, study):
        self.ui.studyname_lineEdit.setText(study.name)
        self.ui.outputdir_lineEdit.setText(study.outputdir)
        self.ui.backup_filename_lineEdit.setText(study.backup_filename)

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
        self._subjects_from_study_dialog.accepted.connect(self.on_subjects_from_study_dialog_accepted)
                                                     
    # this slot is automagically connected
    @QtCore.Slot("const QString &")
    def on_studyname_lineEdit_textChanged(self, text):
        self.enable_apply_button_according_to_lineEdit()

    # this slot is automagically connected
    @QtCore.Slot("const QString &")
    def on_outputdir_lineEdit_textChanged(self, text):
        if self._lineEdit_lock is True: return
        if not self.ui.link_button.isChecked():
            outputdir = self.ui.outputdir_lineEdit.text()
            backup_filename = Study.default_backup_filename_from_outputdir(outputdir)
            self._lineEdit_lock = True
            self.ui.backup_filename_lineEdit.setText(backup_filename)
            self._lineEdit_lock = False 
        self.enable_apply_button_according_to_lineEdit()

    # this slot is automagically connected
    @QtCore.Slot("const QString &")
    def on_backup_filename_lineEdit_textChanged(self, text):
        if self._lineEdit_lock is True: return
        if not self.ui.link_button.isChecked():
            backup_filename = self.ui.backup_filename_lineEdit.text()
            outputdir = Study.default_outputdir_from_backup_filename(backup_filename)
            self._lineEdit_lock = True
            self.ui.outputdir_lineEdit.setText(outputdir)
            self._lineEdit_lock = False 
        self.enable_apply_button_according_to_lineEdit()

    def enable_apply_button_according_to_lineEdit(self):
        status = True
        for lineEdit in [self.ui.outputdir_lineEdit,
                         self.ui.studyname_lineEdit,
                         self.ui.backup_filename_lineEdit]:
            item = lineEdit.text()
            if item == '':
                lineEdit.setStyleSheet(self.error_style_sheet)
                status &= False
            else:
                lineEdit.setStyleSheet(self.default_style_sheet)
        self.ui.apply_button.setEnabled(status)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_outputdir_button_clicked(self):
        caption = 'Select study output directory'
        outputdir = self.ui.outputdir_lineEdit.text()
        if outputdir != '':
            default_directory = outputdir
        else:
            default_directory = os.getcwd()
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                                caption, default_directory) 
        if selected_directory != '':
            self.ui.outputdir_lineEdit.setText(selected_directory)

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
        studyname = self.ui.studyname_lineEdit.text()
        outputdir = self.ui.outputdir_lineEdit.text()
        backup_filename = self.ui.backup_filename_lineEdit.text()
            
        if self._check_study_consistency(outputdir, backup_filename): 
            self.study.name = studyname
            self.study.outputdir = outputdir
            self.study.backup_filename = backup_filename 
            # TODO : update list of subject
            for subject in self._subjects_list:
                self.study.add_subject(subject)
            self.parameter_template = self.ui.parameter_template_combobox.currentText()
            self.ui.accept()

    def on_cancel_button_clicked(self):
        self.ui.reject()

    @QtCore.Slot("const QStringList &")
    def on_select_subjects_dialog_files_selected(self, filenames):
        self._tablemodel.add_subjects_from_filenames(filenames,
                                                    self.default_group)

    def _check_study_consistency(self, outputdir, backup_filename):
        consistency = self._check_valid_outputdir(outputdir)
        if not consistency: return False
        consistency = self._check_valid_backup_filename(backup_filename)
        if not consistency: return False
        consistency = self._check_duplicated_subjects()
        if not consistency: return False
        return True
        
    def _check_valid_outputdir(self, outputdir):
        consistency = True
        msg = ""
        if not os.path.exists(outputdir):
            consistency = False
            msg = "The output directory '%s' does not exist." % outputdir
        elif len(os.listdir(outputdir)) != 0:
            consistency = False
            msg = "The output directory '%s' is not empty." % outputdir
        if not consistency:
            QtGui.QMessageBox.critical(self, "Study consistency error", msg)
        return consistency
            
    def _check_valid_backup_filename(self, backup_filename):
        consistency = True
        backup_filename_directory = os.path.dirname(backup_filename)
        if not os.path.exists(backup_filename_directory):
            consistency = False
            msg = "The backup filename directory '%s' does not exist." % \
                                                backup_filename_directory 
        elif os.path.exists(backup_filename):
            consistency = False
            msg = "The backup filename already '%s' exists." % backup_filename
        if not consistency:
            QtGui.QMessageBox.critical(self, "Study consistency error", msg)
        return consistency
        
    def _check_duplicated_subjects(self):
        if self._subjects_list.is_some_subjects_duplicated():
            QtGui.QMessageBox.critical(self, "Study consistency error",
                                "Some subjects have the same identifier")
            return False
        return True
               

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
