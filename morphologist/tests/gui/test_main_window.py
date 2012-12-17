import sys
import unittest
import os

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui.main_window import create_main_window
from morphologist.tests.gui import TestGui
from morphologist.tests.gui.test_study_editor_widget import TestStudyGui
from morphologist.tests.study import FlatFilesStudyTestCase, BrainvisaStudyTestCase, MockStudyTestCase


class TestStudyWidget(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidget, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()
        if not os.path.exists(self.test_case.outputdir):
            os.makedirs(self.test_case.outputdir)


    def _create_test_case(self):
        raise Exception('TestStudyWidget is an abstract class')

    @TestGui.start_qt_and_test
    def test_start_main_window(self):
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters()
        self.test_case.study.clear_results()
        main_window = create_main_window()
        self.keep_widget_alive(main_window)
        main_window.set_study(self.test_case.study)
        main_window.show()
        model = main_window.study_tablemodel
        subjectnames = [model.data(model.index(i, 0)) \
                        for i in range(model.rowCount())]
        subjectnames = sorted(subjectnames)
        main_window.close()
        self.assertEqual(self.test_case.subjectnames, subjectnames)

    @TestGui.start_qt_and_test
    def test_create_new_study(self):
        main_window = create_main_window()
        self.keep_widget_alive(main_window)
        main_window.show()
        QtTest.QTest.keyClicks(main_window, "n", QtCore.Qt.ControlModifier, 10 )
                                    
        dialog = main_window.findChild(QtGui.QDialog, 'StudyEditorDialog')
        TestStudyGui.action_define_new_study_content(dialog, 
                                                     self.test_case.studyname, 
                                                     self.test_case.outputdir,
                                                     self.test_case.filenames)
        self.assertEqual(main_window.study.name, self.test_case.studyname)
        self.assertEqual(main_window.study.outputdir, self.test_case.outputdir)
        for subjectname in self.test_case.subjectnames:
            subject = main_window.study.subjects.get(subjectname)
            self.assert_(subject is not None)
            self.assert_(os.path.exists(subject.imgname))
            self.assert_(subject.imgname.startswith(self.test_case.outputdir))
        
        main_window.close()


class TestFlatFilesStudyWidget(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestFlatFilesStudyWidget, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = FlatFilesStudyTestCase()
        return test_case


class TestBrainvisaStudyWidget(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestBrainvisaStudyWidget, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = BrainvisaStudyTestCase()
        return test_case


class TestMockStudyWidget(TestStudyWidget):

    def __init__(self, *args, **kwargs):
        super(TestMockStudyWidget, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFlatFilesStudyWidget)
    #FIXME : what to do with this commented lines ?
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestBrainvisaStudyWidget)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMockStudyWidget)
    unittest.TextTestRunner(verbosity=2).run(suite)
