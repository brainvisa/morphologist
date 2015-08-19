import os
import urllib
import zipfile
import shutil
import tempfile
import numpy

from morphologist.core.settings import settings
from morphologist.core.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.core.gui import ui_directory
from morphologist.core.subject import Subject
from morphologist.core.formats import FormatsManager
from morphologist.core.analysis import AnalysisFactory
from morphologist.core.gui.study_editor import StudyEditor, StudyPropertiesEditor
from morphologist.core.gui.study_properties_widget import StudyPropertiesEditorWidget
from morphologist.core.study import Study


class StudyEditorDialog(QtGui.QDialog):
    window_title_from_mode = [\
        "Create a new study",
        "Edit current study"]
    default_group = Subject.DEFAULT_GROUP
    group_column_width = 100

    def __init__(self, study, parent=None, editor_mode=StudyEditor.NEW_STUDY):
        super(StudyEditorDialog, self).__init__(parent)
        self._dialogs = {}
        self._init_ui()
        self.study_editor = StudyEditor(study, editor_mode)
        self._set_window_title(editor_mode)

        self._subjects_tablemodel = SubjectsEditorTableModel(\
                            self.study_editor.subjects_editor)
        self._subjects_tablemodel.rowsRemoved.connect(self.on_subjects_tablemodel_rows_removed)
        self._subjects_tablemodel.rowsInserted.connect(self.on_subjects_tablemodel_rows_inserted)
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
        self._update_nb_subjects_label()
        self._init_subjects_from_directory_dialog(study)
        self._init_db_dialog(settings.study_editor.brainomics)

    def _init_ui(self):
        uifile = os.path.join(ui_directory, 'study_editor_widget.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)
        self.ui.apply_button.clicked.connect(self.on_apply_button_clicked)
        self.ui.cancel_button.clicked.connect(self.on_cancel_button_clicked)

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

    def _init_subjects_from_directory_dialog(self, study):
        output_directory = study.output_directory
        self._subjects_from_directory_dialog \
            = SelectOrganizedDirectoryDialog(
                self.ui, output_directory, study.analysis_type)
        self._subjects_from_directory_dialog.accepted.connect(\
            self.on_subjects_from_directory_dialog_accepted)

    def _set_window_title(self, mode):
        self.setWindowTitle(self.window_title_from_mode[mode])

    @QtCore.Slot("const QModelIndex &", "int", "int")
    def on_subjects_tablemodel_rows_removed(self):
        self._on_table_model_changed()

    @QtCore.Slot("const QModelIndex &", "int", "int")
    def on_subjects_tablemodel_rows_inserted(self):
        self._update_nb_subjects_label()

    @QtCore.Slot()
    def on_subjects_tablemodel_changed(self):
        self._on_table_model_changed()

    def _on_table_model_changed(self):
        self._selection_model.reset()
        empty_item_selection = QtGui.QItemSelection()
        dummy_item_selection = QtGui.QItemSelection()
        self.on_subjects_selection_changed(empty_item_selection,
                                           dummy_item_selection)
        self._update_nb_subjects_label()
                                  
    def _update_nb_subjects_label(self):
        nb_subjects = self._subjects_tablemodel.rowCount()
        nb_selected_subjects = len(self._selection_model.selectedRows())
        nb_subjects_text = "%d selected / %d subject" % (nb_selected_subjects, 
                                                         nb_subjects)
        if nb_subjects > 1:
            nb_subjects_text += "s"
        self.ui.nb_subjects_label.setText(nb_subjects_text)
                        
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
    def on_add_subjects_from_organized_directory_button_clicked(self):
        self._subjects_from_directory_dialog.show()
        
    # this slot is automagically connected
    @QtCore.Slot()
    def on_subjects_from_directory_dialog_accepted(self):
        subjects = self._subjects_from_directory_dialog.get_subjects()
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
        self._update_nb_subjects_label()
           
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_name_button_clicked(self):
        subjectname, ok = QtGui.QInputDialog.getText(self, 
                "Name", "Enter the subject name:")
        if not ok: return
        rows = [index.row() for index in \
                self._selection_model.new_selected_subjects_rows()]
        self._subjects_tablemodel.rename_subjects_name_from_rows(subjectname, rows)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_group_button_clicked(self): 
        groupname, ok = QtGui.QInputDialog.getText(self,
                "Group", "Enter the group name:")
        if not ok: return
        rows = [index.row() for index in \
                self._selection_model.new_selected_subjects_rows()]
        self._subjects_tablemodel.rename_subjects_groupname_from_rows(groupname, rows)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_remove_subjects_button_clicked(self):
        selection = self._selection_model.selection()
        self._subjects_tablemodel.remove_subjects_from_selection(selection)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_subjects_from_database_button_clicked(self):
        self._subject_from_db_dialog.show()
       
    @QtCore.Slot() 
    def on_subject_from_db_dialog_accepted(self):
        self._subjects_tablemodel.add_subjects_from_filenames(\
                            self._subject_from_db_dialog.get_filenames(), 
                            self._subject_from_db_dialog.get_group())

    def on_apply_button_clicked(self):
        if not self._check_study_consistency():
            return

        if self.study_editor.subjects_editor.has_subjects_to_be_removed():
            title = 'Removed subjects from a study'
            msg = 'The following subjects will be removed from the current ' +\
                'study.\nDo you want to remove associated files?'
            msgbox = QtGui.QMessageBox(self)
            msgbox.setWindowTitle(title)
            msgbox.setText(msg)
            cancel_button = msgbox.addButton(QtGui.QMessageBox.Cancel)
            no_button = msgbox.addButton(
                "Keep files", QtGui.QMessageBox.NoRole)
            yes_button = msgbox.addButton(
                "Remove files", QtGui.QMessageBox.YesRole)
            msgbox.setIcon(QtGui.QMessageBox.Question)
            msgbox.exec_()
            answer = msgbox.clickedButton()
            if answer == yes_button:
                study_update_policy \
                    = StudyEditor.ON_SUBJECT_REMOVED_DELETE_FILES
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
        subjects_ok = self._check_study_subjects_consistency()
        if not subjects_ok:
            return False
        properties_ok = self._check_study_properties_consistency()
        return properties_ok

    def _check_study_properties_consistency(self):
        study_properties_editor = self.study_editor.study_properties_editor
        output_directory = study_properties_editor.output_directory
        status = study_properties_editor.get_consistency_status()
        if status == StudyPropertiesEditor.STUDY_PROPERTIES_VALID:
            return True
        elif status & StudyPropertiesEditor.OUTPUTDIR_NOT_EXISTS:
            msg = "The study directory '%s' does not exist." % output_directory +\
            "\nDo you want to create it ?"
            answer = QtGui.QMessageBox.question(self, "Create the study directory ?", msg, 
                                                QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if answer == QtGui.QMessageBox.Ok:
                try:
                    os.makedirs(output_directory)
                except OSError:
                    msg = "The directory %s cannot be created." % output_directory
                else:
                    return True
            else:
                return False
        elif status & StudyPropertiesEditor.OUTPUTDIR_NOT_EMPTY:
            msg = "The study directory '%s' is not empty." % output_directory
        else:
            assert(0)
        QtGui.QMessageBox.critical(self, "Study consistency error", msg)
        return False

    def _check_study_subjects_consistency(self):
        subjects_editor = self.study_editor.subjects_editor
        if subjects_editor.are_some_subjects_duplicated():
            QtGui.QMessageBox.critical(self, "Study consistency error",
                                       "Some subjects have the same identifier")
            return False
        return True
        

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

    # overrided Qt method
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._subjects_editor)

    # overrided Qt method
    def columnCount(self, parent=QtCore.QModelIndex()):
        return 3

    # overrided Qt method
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Vertical:
                return
            elif orientation == QtCore.Qt.Horizontal:
                return self.header[section]

    # overrided Qt method
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

    # overrided Qt method
    def removeRows(self, start_row, count, parent=QtCore.QModelIndex()):
        end_row = start_row + count - 1
        self.beginRemoveRows(parent, start_row, end_row)
        # remove rows from bottom to top to avoid changing the rows indexes
        for row in range(end_row, start_row - 1, -1):
            del self._subjects_editor[row]
        self.endRemoveRows()

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

    def remove_subjects_from_selection(self, selection):
        range_list = []
        for selection_range in selection:
            start_row = selection_range.top()
            count = selection_range.bottom() - start_row + 1
            range_list.append((start_row, count))
        # remove rows from bottom to top to avoid changing the rows indexes
        range_list.sort(reverse=True)
        for start_row, count in range_list:
            self.removeRows(start_row, count)
            

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


class SelectOrganizedDirectoryDialog(QtGui.QDialog):

    def __init__(self, parent, default_directory, analysis_type):
        super(SelectOrganizedDirectoryDialog, self).__init__(parent)

        uifile = os.path.join(ui_directory, 'select_organized_directory.ui')
        self.ui = loadUi(uifile, self)

        self.ui.organized_directory_lineEdit.setText(default_directory)
        self.ui.in_place_checkbox.setVisible(False)

        self._analysis_type = analysis_type

    def get_organized_directory(self):
        return self.ui.organized_directory_lineEdit.text()

    def get_subjects(self):
        organized_directory = self.get_organized_directory()
        analysis_cls = AnalysisFactory.get_analysis_cls(self._analysis_type)
        temp_study = Study('IntraAnalysis',
                           output_directory=organized_directory)
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        subjects = temp_study.get_subjects_from_pattern()
        QtGui.QApplication.restoreOverrideCursor()
        return subjects

    # this slot is automagically connected
    @QtCore.Slot()
    def on_organized_directory_button_clicked(self):
        selected_directory = QtGui.QFileDialog.getExistingDirectory(self.ui,
                                caption="Select a study directory", 
                                directory=self.get_organized_directory(), 
                                options=QtGui.QFileDialog.DontUseNativeDialog)
        if selected_directory != '':
            self.ui.organized_directory_lineEdit.setText(selected_directory)


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
