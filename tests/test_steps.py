import os
import unittest


from steps import BiasCorrection, HistogramAnalysis, BrainSegmentation


class TestSteps(unittest.TestCase):

    def setUp(self):
        base_directory = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition"

        self.mri = os.path.join(base_directory, "icbm100T.ima")
        self.commissure_coordinates = os.path.join(base_directory, "icbm100T.APC") 
        self.hfiltered = os.path.join(base_directory, "default_analysis/hfiltered_icbm100T.ima")
        self.white_ridges = os.path.join(base_directory, "default_analysis/whiteridge_icbm100T.ima")
        self.edges = os.path.join(base_directory, "default_analysis/edges_icbm100T.ima")
        self.mri_corrected = os.path.join(base_directory, "default_analysis/nobias_icbm100T.ima")
        self.variance = os.path.join(base_directory, "default_analysis/variance_icbm100T.ima")
        self.histo_analysis = os.path.join(base_directory, "default_analysis/nobias_icbm100T.han")
        self.brain_mask = os.path.join(base_directory, "default_analysis/segmentation/brain_icbm100T.ima")


    def test_bias_correction(self):
        bias_correction = BiasCorrection()

        bias_correction.mri = self.mri 
        bias_correction.commissure_coordinates = self.commissure_coordinates 

        bias_correction.hfiltered = self.hfiltered 
        bias_correction.white_ridges = self.white_ridges
        bias_correction.edges = self.edges 
        bias_correction.variance = self.variance 
        bias_correction.mri_corrected = self.mri_corrected 

        bias_correction.run()
    
    def test_histogram_analysis(self):
        histo_analysis = HistogramAnalysis()
        
        histo_analysis.mri_corrected = self.mri_corrected 
        histo_analysis.white_ridges = self.white_ridges 
        histo_analysis.hfiltered = self.hfiltered 

        histo_analysis.histo_analysis = self.histo_analysis
    
        histo_analysis.run()
    
    
    def test_brain_segmentation(self):
        brain_segmentation = BrainSegmentation()
    
        brain_segmentation.mri_corrected = self.mri_corrected
        brain_segmentation.commissure_coordinates = self.commissure_coordinates
        brain_segmentation.white_ridges = self.white_ridges
        brain_segmentation.edges = self.edges 
        brain_segmentation.variance = self.variance
        brain_segmentation.histo_analysis = self.histo_analysis

        brain_segmentation.brain_mask = self.brain_mask
    
        brain_segmentation.run()



if __name__ == '__main__':

    unittest.main()

