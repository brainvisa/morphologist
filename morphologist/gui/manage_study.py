import os

from .qt_backend import QtGui, QtCore, loadUi
from .gui import ui_directory
from morphologist.study import Study
from morphologist.formats import FormatsManager


class SelectSubjectsDialog(QtGui.QFileDialog):
    
    def __init__(self, parent):
        caption = "Select one or more subjects to be include into your study"
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


class ManageStudyWindow(QtGui.QDialog):
    on_apply_cancel_buttons_clicked_map = {}
    default_group = 'group 1'
    group_column_width = 100
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2

    @classmethod
    def _init_class(cls):
        apply_role = QtGui.QDialogButtonBox.ApplyRole
        reject_role = QtGui.QDialogButtonBox.RejectRole
        map = cls.on_apply_cancel_buttons_clicked_map
        map[apply_role] = cls.on_apply_button_clicked
        map[reject_role] = cls.on_cancel_button_clicked

    def __init__(self, study, parent=None):
        super(ManageStudyWindow, self).__init__(parent)
        self.study = study
        uifile = os.path.join(ui_directory, 'manage_study.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)

        # TODO : fill tablewidget model with the study content
        self.ui.studyname_lineEdit.setText(self.study.name)
        self.ui.outputdir_lineEdit.setText(self.study.outputdir)

        self._init_ui()

    def _init_ui(self):
        tablewidget = self.ui.subjects_tablewidget
        tablewidget.setColumnWidth(0, ManageStudyWindow.group_column_width)

    def add_subjects(self, filenames, groupname=default_group):
        for filename in filenames:
            self._add_subject(filename, groupname)

    # this slot is automagically connected
    @QtCore.Slot("const QString &")
    def on_studyname_lineEdit_textChanged(self, text):
        self.on_lineEdit_textChanged(text)

    # this slot is automagically connected
    @QtCore.Slot("const QString &")
    def on_outputdir_lineEdit_textChanged(self, text):
        self.on_lineEdit_textChanged(text)

    def on_lineEdit_textChanged(self, text):
        outputdir = self.ui.outputdir_lineEdit.text()
        studyname = self.ui.studyname_lineEdit.text()
        status = (outputdir != '' and studyname != '')
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
        dialog.filesSelected.connect(self.onSelectSubjectsDialogfilesSelected)
        dialog.show()

    # this slot is automagically connected
    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_buttons_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        ManageStudyWindow.on_apply_cancel_buttons_clicked_map[role](self)

    def on_apply_button_clicked(self):
        studyname = self.ui.studyname_lineEdit.text()
        outputdir = self.ui.outputdir_lineEdit.text()
        subjects_data = []
        for i in range(self.ui.subjects_tablewidget.rowCount()):
            subjects_data.append(self._get_subject_data(i))
            
        if self._check_study_consistency(outputdir, subjects_data): 
            self.study.name = studyname
            self.study.outputdir = outputdir
            for groupname, subjectname, filename in subjects_data:
                self.study.add_subject_from_file(filename, subjectname, groupname)
            self.ui.accept()

    def on_cancel_button_clicked(self):
        self.ui.reject()

    @QtCore.Slot("const QStringList &")
    def onSelectSubjectsDialogfilesSelected(self, filenames):
        self.add_subjects(filenames)

    def _check_study_consistency(self, outputdir, subjects_data):
        consistency = True
        consistency &= self._check_valid_outputdir(outputdir)
        consistency &= self._check_duplicated_subjects(subjects_data)
        return consistency
        
    def _check_valid_outputdir(self, outputdir):
        consistency=True
        msg = ""
        if not os.path.exists(outputdir):
            consistency = False
            msg = "The output directory %s does not exist." % outputdir
        elif len(os.listdir(outputdir)) != 0:
            consistency = False
            msg = "The output directory %s is not empty." % outputdir
        if not consistency:
            QtGui.QMessageBox.critical(self, "Study consistency error", msg)
        return consistency
            
        
    def _check_duplicated_subjects(self, subjects_data):
        study_keys = [] #subjectname is the subject uid for now 
        multiples = []
        for groupname, subjectname, filename in subjects_data:
            if subjectname in study_keys and\
               subjectname not in multiples:
                multiples.append(subjectname)
            else:
                study_keys.append(subjectname)
        if multiples: 
            subjectname = multiples[0]
            multiple_str = "%s" %(subjectname)
            for subjectname in multiples[1:len(multiples)]:
                multiple_str += ", %s" %(subjectname)
            QtGui.QMessageBox.critical(self, "Study consistency error",
                                       "Some subjects have the same "
                                       "name: \n %s" %(multiple_str))
            return False
        return True
        
        
    def _add_subject(self, filename, groupname):
        subjectname = Study.define_subjectname_from_filename(filename)
        new_row = self.ui.subjects_tablewidget.rowCount()
        self.ui.subjects_tablewidget.insertRow(new_row)
        if groupname is not None:
            self._fill_groupname(new_row, groupname)
        self._fill_subjectname(new_row, subjectname)
        self._fill_filename(new_row, filename)

    def _fill_groupname(self, subject_index, groupname):
        groupname_item = QtGui.QTableWidgetItem(groupname)
        self.ui.subjects_tablewidget.setItem(subject_index,
            ManageStudyWindow.GROUPNAME_COL, groupname_item)

    def _fill_subjectname(self, subject_index, subjectname):
        subjectname_item = QtGui.QTableWidgetItem(subjectname)
        self.ui.subjects_tablewidget.setItem(subject_index,
            ManageStudyWindow.SUBJECTNAME_COL, subjectname_item)

    def _fill_filename(self, subject_index, filename):
        filename_item = QtGui.QTableWidgetItem(filename)
        self.ui.subjects_tablewidget.setItem(subject_index,
            ManageStudyWindow.FILENAME_COL, filename_item)

    def _get_subject_data(self, subject_index):
        tablewidget = self.ui.subjects_tablewidget
        groupname = tablewidget.item(subject_index,
                        ManageStudyWindow.GROUPNAME_COL).text()
        subjectname = tablewidget.item(subject_index,
                        ManageStudyWindow.SUBJECTNAME_COL).text()
        filename = tablewidget.item(subject_index,
                        ManageStudyWindow.FILENAME_COL).text()
        return groupname, subjectname, filename

ManageStudyWindow._init_class()
