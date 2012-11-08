import unittest
import os

from morphologist.study import Study, Subject, SubjectNameExistsError



class TestStudy(unittest.TestCase):


    def setUp(self):
        self.test_case = self.create_test_case()
        self.study = self.test_case.create_study()
 
  
    def _test_subject_name_exists_error(self):
        existing_subject_name = self.study.list_subject_names()[0]
        
        self.assertRaises(SubjectNameExistsError, 
                          Study.add_subject_from_file,
                          self.study,
                          "/mypath/imgpath", 
                          existing_subject_name) 
 
    def test_run_analyses(self):
        self.study.run_analyses()
        self.study.wait_analyses_end()       

        self.assert_(self.study.analyses_ended_with_success())

    def create_test_case(self):
        test_case = FirstStudyTestCase()
        return test_case


class FirstStudyTestCase(object):

    def __init__(self):
        pass

    def create_study(self):
        output_dir = "/volatile/laguitton/data/icbm/icbm"
        self.study = Study(name="test", outputdir=output_dir)
        subject_names = ["icbm100T", "icbm101T"]
        for subject in subject_names:
            image_path = os.path.join(output_dir, 
                                      subject, 
                                      "t1mri", 
                                      "default_acquisition", 
                                      "%s.ima" % subject) 
            self.study.add_subject_from_file(image_path,
                                             subject,
                                             output_dir)
        self.study.clear_results()
        print self.study
        return self.study


if __name__=='__main__':

    unittest.main()
