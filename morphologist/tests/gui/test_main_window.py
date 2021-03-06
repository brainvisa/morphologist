from __future__ import absolute_import
import sys
import unittest
import os
import time

from morphologist.core.subject import Subject
from morphologist.core.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.core.tests.study import MockStudyTestCase
from morphologist.gui.main_window import MainWindow
from morphologist.tests.gui import TestGui
from morphologist.tests.gui.test_study_editor_widget import TestStudyGui
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCase
from six.moves import range


class TestStudyWidget(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidget, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()
        if not os.path.exists(self.test_case.output_directory):
            os.makedirs(self.test_case.output_directory)


    def _create_test_case(self):
        raise NotImplementedError('TestStudyWidget is an abstract class')

    @TestGui.start_qt_and_test
    def test_start_main_window(self):
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.study.clear_results()
        main_window = MainWindow(self.test_case.analysis_type)
        self.keep_widget_alive(main_window)
        main_window.set_study(self.test_case.study)
        main_window.show()
        model = main_window.study_view.tableview.model()
        subjectnames = [model.data(model.index(i, model.SUBJECTNAME_COL)) \
                        for i in range(model.rowCount())]
        
        main_window.close()
        self.assertEqual(self.test_case.subjectnames, subjectnames)

    @TestGui.start_qt_and_test
    def test_create_new_study(self):
        main_window = MainWindow(self.test_case.analysis_type)
        self.keep_widget_alive(main_window)
        main_window.show()
        QtTest.QTest.keyClicks(main_window, "n", QtCore.Qt.ControlModifier, 10 )
                                    
        dialog = main_window.findChild(QtGui.QDialog, 'StudyEditorDialog')
        TestStudyGui.action_define_new_study_content(dialog, 
                                                     self.test_case.studyname, 
                                                     self.test_case.output_directory,
                                                     self.test_case.filenames)
        import_dialog = main_window.findChild(QtGui.QDialog, 'ImportSubjectsDialog')
        close_button = import_dialog.ui.close_buttonBox
        while not close_button.isEnabled():
            time.sleep(1)
            QtGui.QApplication.processEvents()
        QtTest.QTest.mouseClick(close_button, QtCore.Qt.LeftButton)
        
        self.assertEqual(main_window.study.name, self.test_case.studyname)
        self.assertEqual(main_window.study.output_directory, self.test_case.output_directory)
        self._assert_subjects_exist(main_window.study)
        main_window.close()
        
    def _assert_subjects_exist(self, study):
        for filename in self.test_case.filenames:
            subject = Subject.from_filename(filename)
            subject.groupname = Subject.DEFAULT_GROUP
            subject_id = subject.id()
            self.assert_(subject_id in study.subjects)
            study_subject = study.subjects[subject_id]
            self.assert_(os.path.exists(study_subject.filename))
            self.assert_(study_subject.filename.startswith(self.test_case.output_directory))


class TestStudyWidgetIntraAnalysis(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidgetIntraAnalysis, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = IntraAnalysisStudyTestCase()
        return test_case


class TestMockStudyWidget(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestMockStudyWidget, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudyWidgetIntraAnalysis)
    #suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestMockStudyWidget))
    unittest.TextTestRunner(verbosity=2).run(suite)

