import os
import urllib
import zipfile
import shutil
import tempfile

from morphologist.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.gui import ui_directory
from morphologist.study import Study, Subject
from morphologist.formats import FormatsManager


class StudyEditorDialog(QtGui.QDialog):
    on_apply_cancel_buttons_clicked_map = {}
    default_group = Study.DEFAULT_GROUP
    group_column_width = 100
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2
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

    def __init__(self, study, parent=None, enable_brainomics_db=False):
        super(StudyEditorDialog, self).__init__(parent)
        self.study = study
        self.parameter_template = study.analysis_cls().PARAMETER_TEMPLATES[0]
        self._lineEdit_lock = False
        uifile = os.path.join(ui_directory, 'study_editor_widget.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)

        # TODO : fill tablewidget model with the study content
        self.ui.studyname_lineEdit.setText(self.study.name)
        self.ui.outputdir_lineEdit.setText(self.study.outputdir)
        self.ui.backup_filename_lineEdit.setText(self.study.backup_filename)
        for param_template_name in self.study.analysis_cls().PARAMETER_TEMPLATES:
            self.ui.parameter_template_combobox.addItem(param_template_name)
            if param_template_name == self.parameter_template:
                self.ui.parameter_template_combobox.setCurrentIndex(self.ui.parameter_template_combobox.count()-1)

        tablewidget_header = self.ui.subjects_tablewidget.horizontalHeader()
        tablewidget_header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
        
        self._init_subjects_from_study_dialog()
        self._subject_from_db_dialog = None
        if enable_brainomics_db:
            self.ui.add_subjects_from_database_button.setEnabled(True)
            self._init_db_dialog()
        else:
            self.ui.add_subjects_from_database_button.hide()    

    def _init_db_dialog(self):
        self._subject_from_db_dialog = SubjectsFromDatabaseDialog(self.ui)
        self._subject_from_db_dialog.set_group(self.default_group)
        self._subject_from_db_dialog.set_server_url("http://neurospin-cubicweb.intra.cea.fr:8080")
        self._subject_from_db_dialog.set_rql_request('''Any X WHERE X is Scan, X type "raw T1", X concerns A, A age 25''')
        self._subject_from_db_dialog.accepted.connect(self.on_subject_from_db_dialog_accepted)
             
    def _init_subjects_from_study_dialog(self):
        outputdir = self.study.outputdir
        parameter_templates = self.study.analysis_cls().PARAMETER_TEMPLATES
        selected_template = self.parameter_template
        self._subjects_from_study_dialog = SelectStudyDirectoryDialog(self.ui, outputdir, 
                                            parameter_templates, selected_template)
        self._subjects_from_study_dialog.accepted.connect(self.on_subjects_from_study_dialog_accepted)
                                                     
    def add_subjects_from_filenames(self, filenames, groupname=default_group):
        for filename in filenames:
            subjectname = Study.define_subjectname_from_filename(filename)
            self._add_subject(Subject(groupname, subjectname, filename))

    def add_subjects(self, subjects):
        for subject in subjects:
            self._add_subject(subject)
        
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
            self.add_subjects(subjects)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_name_button_clicked(self):
        subject, ok = QtGui.QInputDialog.getText(self, "Enter the subject name", "Subject name:")
        if ok:
            for selection_range in self.ui.subjects_tablewidget.selectedRanges():
                for row in range(selection_range.topRow(), selection_range.bottomRow()+1):
                    item = self.ui.subjects_tablewidget.item(row, self.SUBJECTNAME_COL)
                    item.setText(subject)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_edit_subjects_group_button_clicked(self): 
        group, ok = QtGui.QInputDialog.getText(self, "Enter the group name", "Group name:")
        if ok:
            for selection_range in self.ui.subjects_tablewidget.selectedRanges():
                for row in range(selection_range.topRow(), selection_range.bottomRow()+1):
                    item = self.ui.subjects_tablewidget.item(row, self.GROUPNAME_COL)
                    item.setText(group)

    # this slot is automagically connected
    @QtCore.Slot()
    def on_remove_subjects_button_clicked(self):
        rows_to_remove = []
        for selection_range in self.ui.subjects_tablewidget.selectedRanges():
            for row in range(selection_range.topRow(), selection_range.bottomRow()+1):
                rows_to_remove.append(row)
        # remove rows from bottom to top to avoid changing the rows indexes
        rows_to_remove.sort(reverse=True)
        for row in rows_to_remove:
            self.ui.subjects_tablewidget.removeRow(row)
    
    # this slot is automagically connected
    @QtCore.Slot()
    def on_add_subjects_from_database_button_clicked(self):
        self._subject_from_db_dialog.show()
       
    @QtCore.Slot() 
    def on_subject_from_db_dialog_accepted(self):
        self.add_subjects_from_filenames(self._subject_from_db_dialog.get_filenames(), 
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
        subjects = []
        for i in range(self.ui.subjects_tablewidget.rowCount()):
            subjects.append(self._get_subject(i))
            
        if self._check_study_consistency(outputdir, subjects, backup_filename): 
            self.study.name = studyname
            self.study.outputdir = outputdir
            self.study.backup_filename = backup_filename 
            for subject in subjects:
                self.study.add_subject(subject)
            self.parameter_template = self.ui.parameter_template_combobox.currentText()
            self.ui.accept()

    def on_cancel_button_clicked(self):
        self.ui.reject()

    @QtCore.Slot("const QStringList &")
    def on_select_subjects_dialog_files_selected(self, filenames):
        self.add_subjects_from_filenames(filenames)

    def _check_study_consistency(self, outputdir,
                subjects_data, backup_filename):
        consistency = self._check_valid_outputdir(outputdir)
        if not consistency: return False
        consistency = self._check_valid_backup_filename(backup_filename)
        if not consistency: return False
        consistency = self._check_duplicated_subjects(subjects_data)
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
        
    def _check_duplicated_subjects(self, subjects):
        processed = []
        multiples = []
        for subject in subjects:
            if subject in processed and\
               subject not in multiples:
                multiples.append(subject)
            else:
                processed.append(subject)
        if multiples: 
            multiple_str = ", ".join([str(subject) for subject in multiples])
            QtGui.QMessageBox.critical(self, "Study consistency error",
                                       "Some subjects have the same "
                                       "identifier: \n %s" %(multiple_str))
            return False
        return True
        
    def _add_subject(self, subject):
        new_row = self.ui.subjects_tablewidget.rowCount()
        self.ui.subjects_tablewidget.insertRow(new_row)
        if subject.groupname is not None:
            self._fill_groupname(new_row, subject.groupname)
        self._fill_subjectname(new_row, subject.subjectname)
        self._fill_filename(new_row, subject.filename)
        
    def _fill_groupname(self, subject_index, groupname):
        groupname_item = QtGui.QTableWidgetItem(groupname)
        self.ui.subjects_tablewidget.setItem(subject_index,
                         self.GROUPNAME_COL, groupname_item)

    def _fill_subjectname(self, subject_index, subjectname):
        subjectname_item = QtGui.QTableWidgetItem(subjectname)
        self.ui.subjects_tablewidget.setItem(subject_index,
                        self.SUBJECTNAME_COL, subjectname_item)

    def _fill_filename(self, subject_index, filename):
        filename_item = QtGui.QTableWidgetItem(filename)
        self.ui.subjects_tablewidget.setItem(subject_index,
                            self.FILENAME_COL, filename_item)
        filename_item.setToolTip(filename)

    def _get_subject(self, subject_index):
        tablewidget = self.ui.subjects_tablewidget
        groupname = tablewidget.item(subject_index, self.GROUPNAME_COL).text()
        subjectname = tablewidget.item(subject_index, self.SUBJECTNAME_COL).text()
        filename = tablewidget.item(subject_index, self.FILENAME_COL).text()
        return Subject(groupname, subjectname, filename)


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
            self.load(self.ui.server_url_lineEdit.text(), 
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
        self.ui.server_url_lineEdit.setText(server_url)

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
