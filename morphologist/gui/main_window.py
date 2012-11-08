import os

from .qt_backend import QtCore, loadUi
from .gui import ui_directory
from ..study import Study


class StudyWidget(object):
    uifile = os.path.join(ui_directory, 'display_study.ui')

    def __init__(self, parent):
        self.ui = loadUi(StudyWidget.uifile, parent)
	

class IntraAnalysisWindow(object):
    uifile = os.path.join(ui_directory, 'intra_analysis.ui')

    def __init__(self):
        self.ui = loadUi(IntraAnalysisWindow.uifile)
        self.study_widget = StudyWidget(self.ui.study_widget_wrapper)
	
        self._init_qt_connections()
        self._init_ui()

    def _init_qt_connections(self):
        self.ui.run_button.clicked.connect(self.on_run_button_clicked)
        self.ui.stop_button.clicked.connect(self.on_stop_button_clicked)

    def _init_ui(self):
        self.ui.setEnabled(True) #FIXME

    @QtCore.Slot()
    def on_run_button_clicked(self):
        print "on_run_button_clicked"

    @QtCore.Slot()
    def on_stop_button_clicked(self):
        print "on_stop_button_clicked"


def create_main_window():
    return IntraAnalysisWindow()
