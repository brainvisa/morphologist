import os, sys
import types
import unittest

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui import ManageStudyWindow
from morphologist.study import Study
from gui import TestGui

class TestStudyGui(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyGui, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()
        self.study = None

    @TestGui.start_qt_and_test
    def test_defining_new_content_for_an_empty_study(self):
        self.study = self._create_empty_study()

        global manage_subjects_window
        manage_subjects_window = ManageStudyWindow(self.study)
        manage_subjects_window.ui.show()
        self.action_define_new_study_content(manage_subjects_window,
            self.test_case.studyname, self.test_case.outputdir,
            self.test_case.filenames)
        manage_subjects_window.ui.close()

        self._assert_study_is_conformed_to_test_case(self.study)

    @TestGui.start_qt_and_test
    def test_loading_study_for_modification(self):
        self.study = self._create_filled_study()

        global manage_subjects_window
        manage_subjects_window = ManageStudyWindow(self.study)
        manage_subjects_window.ui.show()
        manage_subjects_window.ui.close()

        studyname = manage_subjects_window.ui.studyname_lineEdit.text()
        outputdir = manage_subjects_window.ui.outputdir_lineEdit.text()

        self._assert_study_is_conformed_to_test_case(self.study)

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
            if os.path.exists(filename):
                dialog.selectFile(filename)
            else:
                msg = "Error: needed ressource missing : "
                print msg + "'%s'" % filename
            dialog.accept()
            dialog.deleteLater()
            QtGui.qApp.sendPostedEvents(dialog, QtCore.QEvent.DeferredDelete)

        # apply
        QtTest.QTest.mouseClick(ui.apply_button, QtCore.Qt.LeftButton)

    def _create_empty_study(self):
        return Study()

    def _create_filled_study(self):
        study = Study(self.test_case.studyname, self.test_case.outputdir)
        for filename, subjectname, groupname in zip(self.test_case.filenames,
            self.test_case.subjectnames, self.test_case.groupnames):
            study.add_subject_from_file(filename, subjectname, groupname)
        return study

    def _assert_study_is_conformed_to_test_case(self, study):
        self.assertEqual(self.study.name, self.test_case.studyname)
        self.assertEqual(self.study.outputdir, self.test_case.outputdir)


class TestFewSubjectsStudyGui(TestStudyGui):

    def __init__(self, *args, **kwargs):
        super(TestFewSubjectsStudyGui, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = FewSubjectsStudyTestCase()
        return test_case


class AbstractStudyTestCase(object):

    def __init__(self):
        self.studyname = None
        self.outputdir = None
        self.filenames = None
        self.subjectnames = None
        self.groupnames = None


class FewSubjectsStudyTestCase(AbstractStudyTestCase):
    prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

    def __init__(self):
        self.studyname = 'my_study'
        self.outputdir = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/studies/my_study'
        basenames = ['caca.ima', 'chaos.ima.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(FewSubjectsStudyTestCase.prefix,
                                  filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFewSubjectsStudyGui)
    unittest.TextTestRunner(verbosity=2).run(suite)
