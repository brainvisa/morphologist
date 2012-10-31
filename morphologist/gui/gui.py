import os, sys
from qt_backend import QtGui, QtCore, loadUi
from ..study import Study


class SelectSubjectsDialog(QtGui.QFileDialog):
    def __init__(self, manage_subjects_window, subject_manager):
        caption = "Select one or more subjects to be include into your study"
        directory = os.getcwd()
        filter = "3D Volumes (*.nii *.ima)"
        super(SelectSubjectsDialog, self).__init__(manage_subjects_window,
                                                   caption, directory, filter)
        self._subject_manager = subject_manager
        self.setObjectName("SelectSubjectsDialog")
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setFileMode(QtGui.QFileDialog.ExistingFiles)
        self.filesSelected.connect(self.onfilesSelected)
#        self.rejected.connect(self.onRejected)

    @QtCore.Slot("const QStringList &")
    def onfilesSelected(self, list):
        self._subject_manager.add_subjects(list)

#    @QtCore.Slot()
#    def onRejected(self):
#        print "!!!!!!!!!!!!!"
#        print "reject !"
#        print "!!!!!!!!!!!!!"


prefix = os.path.dirname(__file__)
ui_directory = os.path.join(prefix, 'ui')

class ManageSubjectsWindow(object):
    on_apply_cancel_button_clicked_map = {}

    @classmethod
    def _init_class(cls):
        apply_role = QtGui.QDialogButtonBox.ApplyRole
        reject_role = QtGui.QDialogButtonBox.RejectRole
        map = cls.on_apply_cancel_button_clicked_map
        map[apply_role] = cls.on_apply_button_clicked
        map[reject_role] = cls.on_cancel_button_clicked

    def __init__(self, parent=None, study=None):
        ui = os.path.join(ui_directory, 'manage_subjects_of_a_study.ui')
        self.ui = loadUi(ui)
        # TODO : fill tablewidget model with the study content

        tablewidget = self.ui.subjects_tablewidget
        tablewidget.setColumnWidth(0, 50)

        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel

        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)

        self.ui.add_one_subject_from_a_file_button.clicked.connect(\
                self.on_add_one_subject_from_a_file_button_clicked)
        self.ui.apply_cancel_buttons.clicked.connect(\
                self.on_apply_cancel_button_clicked)

    @QtCore.Slot()
    def on_add_one_subject_from_a_file_button_clicked(self):
        dialog = SelectSubjectsDialog(self.ui, self)
        dialog.show()

    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_button_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        ManageSubjectsWindow.on_apply_cancel_button_clicked_map[role](self)

    def on_apply_button_clicked(self):
        print "apply!" #TODO

    def on_cancel_button_clicked(self):
        print "cancel" #TODO

    def add_subjects(self, filenames, groupname=None):
        for filename in filenames:
            self.add_subject(filename, groupname)

    def add_subject(self, filename, groupname=None):
        tablewidget = self.ui.subjects_tablewidget
        tablewidget.insertRow(0)
        if groupname is not None:
            groupname_item = QtGui.QTableWidgetItem(group)
            self.ui.subjects_tablewidget.setItem(0, 0, groupname_item)
        subject_name = os.path.splitext(os.path.basename(filename))[0]
        subjectname_item = QtGui.QTableWidgetItem(subject_name)
        self.ui.subjects_tablewidget.setItem(0, 1, subjectname_item)
        filename_item = QtGui.QTableWidgetItem(filename)
        self.ui.subjects_tablewidget.setItem(0, 2, filename_item)

ManageSubjectsWindow._init_class()
