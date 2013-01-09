import os, sys
import unittest

from morphologist.gui.qt_backend import QtGui, QtCore, QtTest
from morphologist.gui.study_editor_widget import StudyEditorDialog
from morphologist.intra_analysis_study import IntraAnalysisStudy
from morphologist.intra_analysis import IntraAnalysis
from morphologist.tests.gui import TestGui
from morphologist.tests.intra_analysis.study import IntraAnalysisStudyTestCase


class TestStudyGui(TestGui):

    def __init__(self, *args, **kwargs):
        super(TestStudyGui, self).__init__(*args, **kwargs)

    def setUp(self):
        self.test_case = self._create_test_case()

    @TestGui.start_qt_and_test
    def test_defining_new_content_for_an_empty_study(self):
        study = IntraAnalysisStudy()

        manage_subjects_window = StudyEditorDialog(study)
        self.keep_widget_alive(manage_subjects_window)
        manage_subjects_window.ui.show()
        #FIXME: replace manage_subjects_window.ui by manage_subjects_window
        self.action_define_new_study_content(manage_subjects_window.ui,
            self.test_case.studyname, self.test_case.outputdir,
            self.test_case.filenames)
        manage_subjects_window.ui.close()

        self._assert_study_is_conformed_to_test_case(study)

    @TestGui.start_qt_and_test
    def test_loading_study_for_modification(self):
        study = self.test_case.create_study()

        manage_subjects_window = StudyEditorDialog(study)
        self.keep_widget_alive(manage_subjects_window)
        manage_subjects_window.ui.show()
        manage_subjects_window.ui.close()

        self._assert_study_is_conformed_to_test_case(study)
    
    @TestGui.start_qt_and_test        
    def test_changing_parameter_template(self):
        study = self.test_case.create_study()
        parameter_template = IntraAnalysis.DEFAULT_PARAM_TEMPLATE
        study_editor_widget = StudyEditorDialog(study)
        self._action_change_parameter_template(study_editor_widget, parameter_template)
        
        self.assertEqual(study_editor_widget.parameter_template, parameter_template)
                
    @staticmethod
    def action_define_new_study_content(manage_subjects_window_ui,
                                        studyname, outputdir, filenames):
        ui = manage_subjects_window_ui

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

    @staticmethod
    def _action_change_parameter_template(study_editor_widget, parameter_template):
        ui = study_editor_widget.ui
        item_index = ui.parameter_template_combobox.findText(parameter_template)
        ui.parameter_template_combobox.setCurrentIndex(item_index)
        QtTest.QTest.mouseClick(ui.apply_button, QtCore.Qt.LeftButton)

    def _assert_study_is_conformed_to_test_case(self, study):
        self.assertEqual(study.name, self.test_case.studyname)
        self.assertEqual(study.outputdir, self.test_case.outputdir)


class TestIntraAnalysisStudyGui(TestStudyGui):

    def __init__(self, *args, **kwargs):
        super(TestIntraAnalysisStudyGui, self).__init__(*args, **kwargs)

    def _create_test_case(self):
        test_case = IntraAnalysisStudyTestCase()
        return test_case


if __name__ == '__main__':
    qApp = QtGui.QApplication(sys.argv)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisStudyGui)
    unittest.TextTestRunner(verbosity=2).run(suite)
