import os, sys
import types
import unittest

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui import create_main_window
from morphologist.tests.gui import TestGui
from morphologist.tests.study import FlatFilesStudyTestCase, BrainvisaStudyTestCase, MockStudyTestCase

class TestStudyWidget(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyWidget, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()

    @TestGui.start_qt_and_test
    def test_start_main_window(self):
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters()
        self.test_case.study.clear_results()
        global main_window
        main_window = create_main_window()
        main_window.set_study(self.test_case.study)
        main_window.ui.show()
        #main_window.study.
        # main_window.ui.close() #FIXME: uncomment


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
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestBrainvisaStudyWidget)
    #suite = unittest.TestLoader().loadTestsFromTestCase(TestMockStudyWidget)
    unittest.TextTestRunner(verbosity=2).run(suite)
