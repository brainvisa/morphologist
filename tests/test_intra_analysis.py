import unittest
import os

import morphologist_test_settings
from morphologist.analysis import Analysis
from morphologist.intra_analysis import IntraAnalysisStepFlow
from test_analysis import TestAnalysis, AnalysisTestCase, remove_file


class TestIntraAnalysis(TestAnalysis):

    def create_test_case(self):
        test_case = IntraAnalysisTestCase()
        return test_case


class IntraAnalysisTestCase(AnalysisTestCase):

    def __init__(self):
        super(IntraAnalysisTestCase, self).__init__()

    def create_analysis(self):
        intra_analysis_step_flow = IntraAnalysisStepFlow()
        self.analysis = Analysis(intra_analysis_step_flow)
        return self.analysis


    def set_analysis_parameters(self):
        subject = "icbm100T"
        base_directory = "/volatile/laguitton/data/icbm/icbm/%s/t1mri/default_acquisition" % subject
  
        self.analysis.input_params.mri = os.path.join(base_directory, 
                                "%s.ima" % subject)
        self.analysis.input_params.commissure_coordinates = os.path.join(base_directory, 
                                      "%s.APC" % subject) 
        self.analysis.input_params.erosion_size = 1.8  
        self.analysis.input_params.bary_factor = 0.6

        self.analysis.output_params.hfiltered = os.path.join(base_directory, 
                         "default_analysis/hfiltered_%s.ima" % subject)
        self.analysis.output_params.white_ridges = os.path.join(base_directory, 
                            "default_analysis/whiteridge_%s.ima" % subject)
        self.analysis.output_params.edges = os.path.join(base_directory, 
                     "default_analysis/edges_%s.ima" % subject)
        self.analysis.output_params.mri_corrected = os.path.join(base_directory, 
                             "default_analysis/nobias_%s.ima" % subject)
        self.analysis.output_params.variance = os.path.join(base_directory, 
                        "default_analysis/variance_%s.ima" % subject)
        self.analysis.output_params.histo_analysis = os.path.join(base_directory, 
                              "default_analysis/nobias_%s.han" % subject)
        self.analysis.output_params.brain_mask = os.path.join(base_directory, 
                          "default_analysis/segmentation/brain_%s.ima" % subject)
        self.analysis.output_params.split_mask = os.path.join(base_directory, 
                          "default_analysis/segmentation/voronoi_%s.ima" % subject)
        self.analysis.clear_output_files() 


    def delete_some_parameter_values(self):
       self.analysis.output_params.edges = None
       self.analysis.input_params.mri = None


    def delete_some_input_files(self):
        parameter_names = ['mri']
        for name in parameter_names:
            file_name = self.analysis.input_params.get_value(name)
            os.rename(file_name, file_name + "hide_for_test") 


    def create_some_output_files(self):
        parameter_names = ['split_mask', 'variance']
        for name in parameter_names:
            file_name = self.analysis.output_params.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close() 


    def get_wrong_parameter_name(self):
        return "toto"

    def restore_input_files(self):
        parameter_names = ['mri']
        for name in parameter_names:
            file_name = self.analysis.input_params.get_value(name)
            if file_name != None and os.path.isfile(file_name + "hide_for_test"):
                os.rename(file_name + "hide_for_test", file_name) 

       


if __name__ == '__main__':

    #tests = []
    ##tests.append('test_run_analysis')
    ##tests.append('test_analysis_has_run')
    #tests.append('test_stop_analysis')
    ##tests.append('test_clear_state_after_interruption')
    ##tests.append('test_missing_parameter_value_error') 
    ##tests.append('test_missing_input_file_error')
    ##tests.append('test_output_file_exist_error')
    ##tests.append('test_unknown_parameter_error')

    #suite = unittest.TestSuite(map(TestIntraAnalysis, tests))


    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
