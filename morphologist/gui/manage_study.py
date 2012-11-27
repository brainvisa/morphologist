import os

from .qt_backend import QtGui, QtCore, loadUi
from .gui import ui_directory
from morphologist.study import Study
from morphologist.formats import FormatsManager


class SelectSubjectsDialog(QtGui.QFileDialog):
    
    def __init__(self, manage_study_window, study_manager):
        caption = "Select one or more subjects to be include into your study"
        files_filter = self._define_selectable_files_regexp()
        default_directory = ""
        super(SelectSubjectsDialog, self).__init__(manage_study_window,
                                                   caption, default_directory, files_filter)
        self._study_manager = study_manager
        self.setObjectName("SelectSubjectsDialog")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setFileMode(QtGui.QFileDialog.ExistingFiles)
        self.filesSelected.connect(self.onfilesSelected)

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
        all_filters = [all_volumes_filter] + volume_filters + ['All files (*.*)']
        final_filter = ';;'.join(all_filters)
        return final_filter

    @QtCore.Slot("const QStringList &")
    def onfilesSelected(self, filenames):
        self._study_manager.add_subjects(filenames)


class ManageStudyWindow(object):
    on_apply_cancel_button_clicked_map = {}
    default_group = 'group 1'
    group_column_width = 100
    GROUPNAME_COL = 0
    SUBJECTNAME_COL = 1
    FILENAME_COL = 2

    @classmethod
    def _init_class(cls):
        apply_role = QtGui.QDialogButtonBox.ApplyRole
        reject_role = QtGui.QDialogButtonBox.RejectRole
        map = cls.on_apply_cancel_button_clicked_map
        map[apply_role] = cls.on_apply_button_clicked
        map[reject_role] = cls.on_cancel_button_clicked

    def __init__(self, study, parent=None):
        self.study = study
        uifile = os.path.join(ui_directory, 'manage_study.ui')
        self.ui = loadUi(uifile, parent)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)

        # TODO : fill tablewidget model with the study content
        self.ui.studyname_lineEdit.setText(self.study.name)
        self.ui.outputdir_lineEdit.setText(self.study.outputdir)

        self._init_qt_connections()
        self._init_ui()

    def _init_qt_connections(self):
        self.ui.studyname_lineEdit.textChanged.connect(\
                self.on_lineEdit_changed)
        self.ui.outputdir_lineEdit.textChanged.connect(\
                self.on_lineEdit_changed)
        self.ui.outputdir_button.clicked.connect(\
                self.on_outputdir_button_clicked)
        self.ui.add_one_subject_from_a_file_button.clicked.connect(\
                self.on_add_one_subject_from_a_file_button_clicked)
        self.ui.apply_cancel_buttons.clicked.connect(\
                self.on_apply_cancel_button_clicked)

    def _init_ui(self):
        tablewidget = self.ui.subjects_tablewidget
        tablewidget.setColumnWidth(0, ManageStudyWindow.group_column_width)

    def add_subjects(self, filenames, groupname=default_group):
        for filename in filenames:
            self._add_subject(filename, groupname)

    @QtCore.Slot("QString &")
    def on_lineEdit_changed(self, text):
        outputdir = self.ui.outputdir_lineEdit.text()
        studyname = self.ui.studyname_lineEdit.text()
        status = (outputdir != '' and studyname != '')
        self.ui.apply_button.setEnabled(status)

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

    @QtCore.Slot()
    def on_add_one_subject_from_a_file_button_clicked(self):
        dialog = SelectSubjectsDialog(self.ui, self)
        dialog.show()

    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_button_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        ManageStudyWindow.on_apply_cancel_button_clicked_map[role](self)

    def on_apply_button_clicked(self):
        outputdir = self.ui.outputdir_lineEdit.text()
        studyname = self.ui.studyname_lineEdit.text()
        if self._check_study_consistency(): 
            self.study.name = studyname
            self.study.outputdir = outputdir
            for i in range(self.ui.subjects_tablewidget.rowCount()):
                groupname, subjectname, filename = self._get_subject_data(i)
                self.study.add_subject_from_file(filename, subjectname, groupname)
            self.ui.accept()

    def _check_study_consistency(self):
        study_keys = [] #subjectname is the subject uid for now 
        multiples = []
        for i in range(self.ui.subjects_tablewidget.rowCount()):
            groupname, subjectname, filename = self._get_subject_data(i)
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
            QtGui.QMessageBox.critical(self.ui, "Study consistency error",
                                       "Some subjects have the same "
                                       "name: \n %s" %(multiple_str))
            return False
        return True

    def on_cancel_button_clicked(self):
        print "cancel" #TODO
        self.ui.reject()

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
