import unittest
import os
import filecmp
import shutil
import six

from morphologist.core.study import SubjectExistsError
from morphologist.core.subject import Subject
from morphologist.core.study import Study
from morphologist.core.tests.study import MockStudyTestCase
from morphologist.core.tests.mocks.study import MockStudy


class TestStudy(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.study = self.test_case.study
        self.subject = Subject(self.test_case.subjectnames[0], 
                               self.test_case.groupnames[0], 
                               self.test_case.filenames[0]) 

    def tearDown(self):
        shutil.rmtree(self.study.output_directory)
 
    def create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case

    def test_subject_exists_error(self):
        self.study.add_subject(self.subject)

        self.assertRaises(SubjectExistsError, 
                          self.study.add_subject,
                          self.subject) 

    def test_save_load_study(self):
        self.test_case.add_subjects()

        studyfilepath = self.study.backup_filepath
        studyfilepath2 = studyfilepath + "_2"
        if os.path.isfile(studyfilepath): os.remove(studyfilepath)
        if os.path.isfile(studyfilepath2): os.remove(studyfilepath2)
        self.study.save_to_backup_file()
        shutil.move(studyfilepath, studyfilepath2)

        loaded_study = Study.from_file(studyfilepath2)
        loaded_study.save_to_backup_file()

        self.assert_(filecmp.cmp(studyfilepath, studyfilepath2))

    def test_has_subjects(self):
        self.assert_(not self.study.has_subjects())

        self.study.add_subject(self.subject)

        self.assert_(self.study.has_subjects())

    def test_has_some_results(self):
        self.test_case.add_subjects()
        self.test_case.create_some_output_files()

        self.assert_(self.study.has_some_results())

    def test_remove_subject(self):
        self.study.add_subject(self.subject)
        self.study.remove_subject_from_id(self.subject.id())

        self.assert_(not self.study.has_subjects())

    def test_create_study_from_organized_directory(self):
        self.test_case.add_subjects()
        new_study = MockStudy.from_organized_directory(
            self.study.analysis_type, self.study.output_directory)
        self._assert_same_studies(new_study, self.study)

    def _assert_same_studies(self, study_a, study_b):
        self.assert_(study_a.output_directory == study_b.output_directory)
        self.assert_(len(study_a.subjects) == len(study_b.subjects))

        for subject_id, subject_a in six.iteritems(study_a.subjects):
            subject_b = study_b.subjects[subject_id]
            self.assert_(subject_a == subject_b)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudy)
    unittest.TextTestRunner(verbosity=2).run(suite)
    os.unlink('/tmp/mock_fom.json')
