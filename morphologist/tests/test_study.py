import unittest
import os
import filecmp

from morphologist.study import Study, SubjectNameExistsError
from morphologist.tests.study import BrainvisaStudyTestCase, MockStudyTestCase

class TestStudy(unittest.TestCase):


    def setUp(self):
        self.test_case = self.create_test_case()
        self.test_case.create_study()
        self.test_case.add_subjects()
        self.test_case.set_parameters() 
        self.study = self.test_case.study
  
    def test_subject_name_exists_error(self):
        existing_subject_name = self.study.list_subject_names()[0]
        
        self.assertRaises(SubjectNameExistsError, 
                          Study.add_subject_from_file,
                          self.study,
                          "/mypath/imgpath", 
                          existing_subject_name) 
 
    def test_run_analyses(self):
        self.study.clear_results()
        self.study.run_analyses()
        self.study.wait_analyses_end()       

        self.assert_(self.study.analyses_ended_with_success())


    def test_save_load_study(self):
        studyfilepath = os.path.join(self.study.outputdir, "test_study_file")
        studyfilepath2 = studyfilepath + "_2"
        if os.path.isfile(studyfilepath): os.remove(studyfilepath)
        if os.path.isfile(studyfilepath2): os.remove(studyfilepath2)
        print "save to " + repr(studyfilepath)

        self.study.save_to_file(studyfilepath)
        loaded_study = Study.from_file(studyfilepath)
        loaded_study.save_to_file(studyfilepath2)

        self.assert_(filecmp.cmp(studyfilepath, studyfilepath2))


    def create_test_case(self):
        #test_case = BrainvisaStudyTestCase()
        test_case = MockStudyTestCase()
        return test_case


if __name__=='__main__':

    unittest.main()
