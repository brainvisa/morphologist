import os, sys
import types
import unittest
sys.path += ['.']

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui import ManageSubjectsWindow
from morphologist.study import Study


prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'


class GuiTestCase(unittest.TestCase):
    @staticmethod
    def start_qt_and_test(test):
        def func(self):
            qApp = QtGui.QApplication(sys.argv)
            timer = QtCore.QTimer()
            func = types.MethodType(test, self, self.__class__)
            timer.singleShot(0, func)
            self.assertFalse(qApp.exec_())
        return func


class StudyGuiTestCase(GuiTestCase):
    def __init__(self, *args, **kwargs):
        super(StudyGuiTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        self.study = None

    def action_define_new_study_content(self, manage_subjects_window,
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

    @GuiTestCase.start_qt_and_test
    def test_defining_new_content_for_an_empty_study(self):
        self.study = self._create_empty_study()
        filenames = [os.path.join(prefix, filename) for filename in \
            ['caca.ima', 'chaos.ima.gz', 'dionysos2.ima', 'hyperion.nii']]
        studyname = 'my_study'
        outputdir = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/studies/my_study'
        global manage_subjects_window
        manage_subjects_window = ManageSubjectsWindow(self.study)
        manage_subjects_window.ui.show()
        self.action_define_new_study_content(manage_subjects_window,
                        studyname, outputdir, filenames)
        manage_subjects_window.ui.close()

        subjects = None #FIXME
        self.assert_study_equal(self.study, studyname, outputdir, subjects)

    @GuiTestCase.start_qt_and_test
    def test_loading_study_for_modification(self):
        self.study = self._create_filled_study()

        global manage_subjects_window
        manage_subjects_window = ManageSubjectsWindow(self.study)
        manage_subjects_window.ui.show()
        manage_subjects_window.ui.close()

        studyname = manage_subjects_window.ui.studyname_lineEdit.text()
        outputdir = manage_subjects_window.ui.outputdir_lineEdit.text()

        subjects = None #FIXME
        self.assert_study_equal(self.study, studyname, outputdir, subjects)

    def _create_empty_study(self):
        return Study()

    def _create_filled_study(self):
        studyname = 'my_study'
        outputdir = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/studies/my_study'
        study = Study(studyname, outputdir)
        filenames = [os.path.join(prefix, filename) for filename in \
            ['caca.ima', 'chaos.ima.gz', 'dionysos2.ima', 'hyperion.nii']]
        subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        groupnames = ['group 1', 'group 2', 'group 3', 'group 4']
        for filename, subjectname, groupname in zip(filenames,
                                    subjectnames, groupnames):
            study.add_subject_from_file(filename, subjectname, groupname)
        return study

    def assert_study_equal(self, study, studyname, outputdir, subjects):
        self.assertEqual(self.study.name, studyname)
        self.assertEqual(self.study.outputdir, outputdir)
        # FIXME : test subjects

if __name__ == '__main__':
    unittest.main()
