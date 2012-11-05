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

def define_new_study_content(manage_subjects_window,
                studyname, outputdir, filenames):
    ui = manage_subjects_window.ui

    # set studyname and output dir
    ui.studyname_lineEdit.setText(studyname)
    ui.outputdir_lineEdit.setText(outputdir)

    # select some subjects
    for filename in filenames:
        QtTest.QTest.mouseClick(ui.add_one_subject_from_a_file_button,
                                QtCore.Qt.LeftButton)
        dialog = ui.findChild(QtGui.QFileDialog, 'SelectSubjectsDialog')
        dialog.selectFile(filename)
        dialog.accept()
        dialog.deleteLater()
        QtGui.qApp.sendPostedEvents(dialog, QtCore.QEvent.DeferredDelete)

    # apply
    QtTest.QTest.mouseClick(ui.apply_button, QtCore.Qt.LeftButton)


prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

def test_ManageSubjectsWindow():
    filenames = [os.path.join(prefix, filename) for filename in \
                ['caca.ima', 'chaos.ima.gz', 'dionysos2.ima', 'hyperion.nii']]
    studyname = 'my_study'
    outputdir = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/studies/my_study'
    study = Study(studyname)

    global manage_subjects_window

    print "** study before = \n", study
    manage_subjects_window = ManageSubjectsWindow(study)
    manage_subjects_window.ui.show()
    define_new_study_content(manage_subjects_window,
                    studyname, outputdir, filenames)
    print "** study after = \n", study
    manage_subjects_window.ui.close()
    QtGui.qApp.quit()

test_gui(test_ManageSubjectsWindow)
