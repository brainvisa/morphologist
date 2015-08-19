import os
import validate
import multiprocessing

from morphologist.core.settings import settings, AUTO
from morphologist.core.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.core.gui import ui_directory


class RunnerSettingsDialog(QtGui.QDialog):
    def __init__(self, settings, study, parent=None):
        super(RunnerSettingsDialog, self).__init__(parent)
        self._runner_settings = settings.runner.copy()
        self.study = study
        self._init_ui()

    def _init_ui(self):
        uifile = os.path.join(ui_directory, 'runner_settings_widget.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)
        self.ui.apply_button.clicked.connect(self.on_apply_button_clicked)
        self.ui.cancel_button.clicked.connect(self.on_cancel_button_clicked)
        cpus = self._runner_settings.selected_processing_units_n
        if cpus.is_auto:
            self.ui.auto_checkBox.setCheckState(QtCore.Qt.Checked)
        self.ui.selected_cpu_spinBox.setValue(cpus)
        max_cpu = multiprocessing.cpu_count()
        self.ui.selected_cpu_spinBox.setRange(1, max_cpu)
        self.ui.max_cpu_number_label.setText(str(max_cpu))
        if cpus <= max_cpu:
            self.ui.cpu_config_error_label.hide()
            self.ui.cpu_config_error_number_label.hide()
        else:
            self.ui.cpu_config_error_number_label.setText(str(cpus))
        self._create_computing_resources_combobox()
        #self.ui.computing_resource_combobox.currentIndexChanged.connect(
            #self.on_computing_resource_combobox_currentIndexChanged)

    def _create_computing_resources_combobox(self):
        study = self.study
        available_computing_resources \
            = study.get_available_computing_resources()
        for resource_name in available_computing_resources:
            self.ui.computing_resource_combobox.addItem(resource_name)
        self.ui.computing_resource_combobox.setCurrentIndex(
            available_computing_resources.index(
                study.somaworkflow_computing_resource))

    # this slot is automagically connected
    @QtCore.Slot('int')
    def on_auto_checkBox_stateChanged(self, state):
        self.ui.cpu_groupBox.setEnabled(not self._is_auto_mode_on())
        if self._is_auto_mode_on():
            self._runner_settings.selected_processing_units_n = AUTO
        else:
            value = self.ui.selected_cpu_spinBox.value()
            self._runner_settings.selected_processing_units_n = value
        
    # this slot is automagically connected
    @QtCore.Slot('int')
    def on_selected_cpu_spinBox_valueChanged(self, value):
        self._runner_settings.selected_processing_units_n = value

    @QtCore.Slot()
    def on_apply_button_clicked(self):
        if self.study.somaworkflow_computing_resource \
                != self.ui.computing_resource_combobox.currentText():
            print 'computing resource changed'
            self.study.somaworkflow_computing_resource \
                = self.ui.computing_resource_combobox.currentText()
            try:
                self.study.save_to_backup_file()
            except StudySerializationError, e:
                pass  # study is not saved, don't notify

        if self._are_settings_unchanged():
            self.ui.accept()
            return
        title = 'Save settings'
        msg = 'Save cpu settings ?'
        answer = QtGui.QMessageBox.question(self, title, msg,
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | \
            QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
        if answer == QtGui.QMessageBox.Cancel:
            return
        if self._is_auto_mode_on():
            self._runner_settings.selected_processing_units_n = AUTO
        settings.runner.update(self._runner_settings)
        if answer == QtGui.QMessageBox.Yes:
            settings.runner.save()
        self.ui.accept()

    def _are_settings_unchanged(self):
        old_value = settings.runner.selected_processing_units_n
        edited_value = self._runner_settings.selected_processing_units_n
        is_both_auto_mode_on = (old_value.is_auto and edited_value.is_auto)
        is_both_auto_mode_off_and_values_unchanged = (not old_value.is_auto and\
                        not edited_value.is_auto and old_value == edited_value)
        are_settings_unchanged = is_both_auto_mode_on or \
                                 is_both_auto_mode_off_and_values_unchanged
        return are_settings_unchanged

    def _is_auto_mode_on(self):
        return (self.ui.auto_checkBox.checkState() == QtCore.Qt.Checked)

    @QtCore.Slot()
    def on_cancel_button_clicked(self):
        self.ui.reject()
