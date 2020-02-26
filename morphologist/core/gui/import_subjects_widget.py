from __future__ import absolute_import
import os
import time

from morphologist.core.gui.qt_backend import QtGui, QtCore, loadUi
from morphologist.core.gui import ui_directory
from morphologist.core.utils.design_patterns import Observer, \
                                        ObserverNotification
from morphologist.core.gui.study_editor import ImportationStartNotification, \
                                        ImportationStartSubjectNotification, \
                                        ImportationEndSubjectNotification, \
                                        ImportationEndNotification


class ImportSubjectsDialog(QtGui.QDialog, Observer):
    notified = QtCore.pyqtSignal(ObserverNotification)
    details_text_width = 45
    max_subject_repr_len = details_text_width - 5

    def __init__(self, study_editor, parent=None):
        super(ImportSubjectsDialog, self).__init__(parent)
        self._observee = study_editor
        self._observed_subjects_n = 0
        self._init_ui()
        self._observee.add_observer(self)
        self._details_text = ''
        self.notified.connect(self._on_notified)

    def _init_ui(self):
        uifile = os.path.join(ui_directory, 'import_subjects_widget.ui')
        self.ui = loadUi(uifile, self)
        wflags = self.ui.windowFlags()
        self.ui.setWindowFlags(wflags & ~QtCore.Qt.WindowCloseButtonHint \
                                      & ~QtCore.Qt.WindowSystemMenuHint)
        self.on_show_details_button_toggled(False)
        self.ui.progressbar.setValue(self._observed_subjects_n)

    # this slot is automagically connected
    @QtCore.Slot("QAbstractButton *")
    def on_close_buttonBox_clicked(self, button):
        self._observee.remove_observer(self)
        self.ui.accept()

    # this slot is automagically connected
    @QtCore.Slot("bool")
    def on_show_details_button_toggled(self, checked):
        if checked:
            text = '-'
            visible = True
            size_constraint = QtGui.QLayout.SetMinimumSize
        else:
            text = '+'
            visible = False
            size_constraint = QtGui.QLayout.SetFixedSize
        self.ui.show_details_button.setText(text) 
        self.ui.details_textedit.setVisible(visible)
        self.ui.layout().setSizeConstraint(size_constraint)
        self.ui.adjustSize() # warning: min/max size are fixed by this line
        if checked:
            self.ui.setMinimumHeight(0)
            self.ui.setMaximumHeight(16777215)

    # TODO : add comment
    def on_notify_observers(self, notification):
        self.notified.emit(notification)

    @QtCore.Slot(ObserverNotification)
    def _on_notified(self, notification):
        if isinstance(notification, ImportationStartNotification):
            range_max = notification.subjects_to_be_imported_n
            self.ui.progressbar.setRange(0, range_max)
        elif isinstance(notification, ImportationStartSubjectNotification):
            subject_repr = self._subject_repr(notification.subject)
            text = '%s' % subject_repr
            dots = '.' * (self.details_text_width - len(text))
            self._details_text += text + dots
            self._update_details()
        elif isinstance(notification, ImportationEndSubjectNotification):
            if notification.status_ok:
                status_text = '....<span style="color:#00FF00">OK</span>'
            else:
                status_text = '<span style="color:#FF0000">FAILED</span>'
            self._details_text += status_text + '<p></p>\n'
            self._update_details()
            self._observed_subjects_n += 1
            self.ui.progressbar.setValue(self._observed_subjects_n)
        elif isinstance(notification, ImportationEndNotification):
            self.ui.close_buttonBox.setEnabled(True)

    def _subject_repr(self, subject):
        filename = os.path.basename(subject.filename)
        if len(filename) > self.details_text_width:
            filename = filename[:max_subject_repr_len]
        return "%s/%s: %s" % (subject.groupname, subject.name, filename)

    def _update_details(self):
        html = '<html><body style="font-size:10pt; font-weight:400; ' + \
               'font-style:normal; font-family:monospace">' + \
               '%s</body></html>' % self._details_text
        self.ui.details_textedit.setHtml(html)
