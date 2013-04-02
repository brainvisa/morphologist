import os
import validate

from morphologist.core.settings import settings, AUTO
from morphologist.core.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.core.gui import ui_directory


class RunnerSettingsDialog(QtGui.QDialog):
    on_apply_cancel_buttons_clicked_map = {}

    @classmethod
    def _init_class(cls):
        apply_role = QtGui.QDialogButtonBox.ApplyRole
        reject_role = QtGui.QDialogButtonBox.RejectRole
        role_map = cls.on_apply_cancel_buttons_clicked_map
        role_map[apply_role] = cls.on_apply_button_clicked
        role_map[reject_role] = cls.on_cancel_button_clicked

    def __init__(self, settings, parent=None):
        super(RunnerSettingsDialog, self).__init__(parent)
        self._runner_settings = settings.runner.copy()
        self._init_ui()

    def _init_ui(self):
        uifile = os.path.join(ui_directory, 'runner_settings_widget.ui')
        self.ui = loadUi(uifile, self)
        apply_id = QtGui.QDialogButtonBox.Apply
        cancel_id = QtGui.QDialogButtonBox.Cancel
        self.ui.apply_button = self.ui.apply_cancel_buttons.button(apply_id)
        self.ui.cancel_button = self.ui.apply_cancel_buttons.button(cancel_id)
        self.apply_button = self.ui.apply_button
        self.cancel_button = self.ui.cancel_button
        # TODO: for cpu_count(), ask Runner backend instead
        cpus = self._runner_settings.selected_processing_units_n
        if cpus.is_auto:
            self.ui.auto_checkBox.setCheckState(QtCore.Qt.Checked)
        self.ui.selected_cpu_spinBox.setValue(cpus)
        import multiprocessing
        max_cpu = multiprocessing.cpu_count()
        self.ui.selected_cpu_spinBox.setRange(1, max_cpu)
        self.ui.max_cpu_number_label.setText(str(max_cpu))
        if cpus <= max_cpu:
            self.ui.cpu_config_error_label.hide()
            self.ui.cpu_config_error_number_label.hide()
        else:
            self.ui.cpu_config_error_number_label.setText(str(cpus))
            

    # this slot is automagically connected
    @QtCore.Slot('int')
    def on_auto_checkBox_stateChanged(self, state):
        self.ui.cpu_groupBox.setEnabled(not self._is_auto_mode_on())
        
    # this slot is automagically connected
    @QtCore.Slot('int')
    def on_selected_cpu_spinBox_valueChanged(self, value):
        self._runner_settings.selected_processing_units_n = value

    # this slot is automagically connected
    @QtCore.Slot("QAbstractButton *")
    def on_apply_cancel_buttons_clicked(self, button):
        role = self.ui.apply_cancel_buttons.buttonRole(button)
        self.on_apply_cancel_buttons_clicked_map[role](self)

    @QtCore.Slot()
    def on_apply_button_clicked(self):
        current_value = settings.runner.selected_processing_units_n
        edited_value = self._runner_settings.selected_processing_units_n
        is_auto_mode_on_and_unchanged = (current_value.is_auto and \
                                        self._is_auto_mode_on())
        is_auto_mode_off_and_values_unchanged = (not current_value.is_auto and \
                not self._is_auto_mode_on() and current_value == edited_value)
        
        if is_auto_mode_on_and_unchanged or \
            is_auto_mode_off_and_values_unchanged:
            self.ui.accept() # nothing to do
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

    def _is_auto_mode_on(self):
        return (self.ui.auto_checkBox.checkState() == QtCore.Qt.Checked)

    @QtCore.Slot()
    def on_cancel_button_clicked(self):
        self.ui.reject()


RunnerSettingsDialog._init_class()
