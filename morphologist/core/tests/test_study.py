import unittest
import os
import filecmp

from morphologist.core.study import SubjectExistsError
from morphologist.core.tests.study import MockStudyTestCase


class TestStudy(unittest.TestCase):

    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters() 
        self.study = self.test_case.study
 
    def test_subject_exists_error(self):
        existing_subject = self.study.subjects[0]
        
        self.assertRaises(SubjectExistsError, 
                          self.test_case.study_cls().add_subject,
                          self.study,
                          existing_subject) 
   
    def test_save_load_study(self):
        studyfilepath = self.study.backup_filename
        studyfilepath2 = studyfilepath + "_2"
        if os.path.isfile(studyfilepath): os.remove(studyfilepath)
        if os.path.isfile(studyfilepath2): os.remove(studyfilepath2)
        print "save to " + repr(studyfilepath)

        self.study.save_to_backup_file()
        loaded_study = self.test_case.study_cls().from_file(studyfilepath)
        loaded_study.backup_filename = studyfilepath2
        loaded_study.save_to_backup_file()

        self.assert_(filecmp.cmp(studyfilepath, studyfilepath2))

    def create_test_case(self):
        test_case = MockStudyTestCase()
        return test_case


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStudy)
    unittest.TextTestRunner(verbosity=2).run(suite)
