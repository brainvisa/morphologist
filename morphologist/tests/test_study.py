import unittest
import os

from morphologist.study import Study, Subject, SubjectNameExistsError



class TestStudy(unittest.TestCase):


    def setUp(self):
        self.test_case = self.create_test_case()
        self.study = self.test_case.create_study()
 
  
    def test_subject_name_exists_error(self):
        existing_subject_name = self.study.list_subject_names()[0]
        
        self.assertRaises(SubjectNameExistsError, 
                          Study.add_subject_from_file,
                          self.study,
                          "/mypath/imgpath", 
                          existing_subject_name) 
 

    def create_test_case(self):
        test_case = FirstStudyTestCase()
        return test_case


class FirstStudyTestCase(object):

    def __init__(self):
        pass

    def create_study(self):
        self.study = Study()
        subject_names = ["icbm100T", "icbm101T"]
        for subject in subject_names:
            base_directory = "/volatile/laguitton/data/icbm/icbm/%s/t1mri/default_acquisition" % subject
            image_path = os.path.join(base_directory, "%s.ima" % subject)
            self.study.add_subject_from_file(image_path,
                                             subject)
        print self.study
        return self.study

    def get_existing_subject_name(self):
        return "icbm100T"


if __name__=='__main__':

    unittest.main()
