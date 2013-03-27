import unittest
import os
import filecmp

from morphologist.core.study import SubjectExistsError
from morphologist.core.subject import Subject
from morphologist.core.study import Study
from morphologist.core.tests.study import MockStudyTestCase


class TestStudy(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.study = self.test_case.study
        self.subject = Subject(self.test_case.subjectnames[0], 
                               self.test_case.groupnames[0], 
                               self.test_case.filenames[0]) 
 
    def test_subject_exists_error(self):
        self.study.add_subject(self.subject)
        
        self.assertRaises(SubjectExistsError, 
                          self.study.add_subject,
                          self.subject) 
   
    def test_save_load_study(self):
        self.test_case.add_subjects()
        
        studyfilepath = self.study.backup_filename
        studyfilepath2 = studyfilepath + "_2"
        if os.path.isfile(studyfilepath): os.remove(studyfilepath)
        if os.path.isfile(studyfilepath2): os.remove(studyfilepath2)
        self.study.save_to_backup_file()
        
        loaded_study = Study.from_file(studyfilepath)
        loaded_study.backup_filename = studyfilepath2
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
        
    def create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudy)
    unittest.TextTestRunner(verbosity=2).run(suite)
