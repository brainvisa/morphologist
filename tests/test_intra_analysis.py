import unittest
import os

from morphologist.analysis import Analysis
from morphologist.intra_analysis import IntraAnalysisStepFlow
from test_analysis import TestAnalysis, AnalysisTestCase


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
        base_directory = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition"
        subject = "icbm100T"
  
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
       #TODO
        pass

    def delete_some_input_files(self):
       #TODO
        pass

    def create_some_output_files(self):
       #TODO
        pass

    def get_wrong_parameter_name(self):
       #TODO
        pass



if __name__ == '__main__':

    suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysis)
    unittest.TextTestRunner(verbosity=2).run(suite)
