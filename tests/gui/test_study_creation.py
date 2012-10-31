import os, sys
sys.path += ['.']

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui import ManageSubjectsWindow
from morphologist.study import Study

def test_gui(test):
    qApp = QtGui.QApplication(sys.argv)
    timer = QtCore.QTimer()
    timer.singleShot(0, test) 
    sys.exit(qApp.exec_())

prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

def action_select_some_input_subjects(manage_subjects_window):
    ui = manage_subjects_window.ui
    for filename in ['caca.ima', 'chaos.ima.gz',
                     'dionysos2.ima', 'hyperion.nii']:
        QtTest.QTest.mouseClick(ui.add_one_subject_from_a_file_button,
                                QtCore.Qt.LeftButton)
        dialog = ui.findChild(QtGui.QFileDialog, 'SelectSubjectsDialog')
        full_name = os.path.join(prefix, filename)
        dialog.selectFile(full_name)
        dialog.accept()
        dialog.deleteLater()
        QtGui.qApp.sendPostedEvents(dialog, QtCore.QEvent.DeferredDelete)


def test_ManageSubjectsWindow():
    study = Study('my_study')

    global manage_subjects_window

    manage_subjects_window = ManageSubjectsWindow()
    manage_subjects_window.ui.show()
    action_select_some_input_subjects(manage_subjects_window)
    #window.ui.close()
    #QtTest.QTest.mouseClick(window.apply_button, QtCore.Qt.LeftButton)
    #QtGui.qApp.quit()

test_gui(test_ManageSubjectsWindow)
