import os
import unittest
import shutil

from morphologist.steps import SpatialNormalization, BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain

class TestIntraAnalysisSteps(unittest.TestCase):

    def setUp(self):
        
        self.subject = "hyperion"
        self.base_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/test/%s/t1mri/default_acquisition" % self.subject
        self.output_directory = "/tmp/morphologist_test_steps"
        
        if os.path.exists(self.output_directory):
            shutil.rmtree(self.output_directory)
        os.makedirs(self.output_directory)
  
        self.mri = os.path.join(self.base_directory, 
                                "%s.nii" % self.subject)
        self.commissure_coordinates = os.path.join(self.base_directory, 
                                      "%s.APC" % self.subject) 
        
        if not os.path.exists(os.path.join(self.output_directory, "registration")):
            os.mkdir(os.path.join(self.output_directory, "registration"))

        self.talairach_transform = os.path.join(self.output_directory, 
                                   "registration/RawT1-%s_default_acquisition_TO_Talairach-MNI.trm" % self.subject)
        
        if not os.path.exists(os.path.join(self.output_directory, "default_analysis")):
            os.mkdir(os.path.join(self.output_directory, "default_analysis"))
        self.hfiltered = os.path.join(self.output_directory, 
                         "default_analysis/hfiltered_%s.nii" % self.subject)
        self.white_ridges = os.path.join(self.output_directory, 
                            "default_analysis/whiteridge_%s.nii" % self.subject)
        self.edges = os.path.join(self.output_directory, 
                     "default_analysis/edges_%s.nii" % self.subject)
        self.mri_corrected = os.path.join(self.output_directory, 
                             "default_analysis/nobias_%s.nii" % self.subject)
        self.variance = os.path.join(self.output_directory, 
                        "default_analysis/variance_%s.nii" % self.subject)
        self.histo_analysis = os.path.join(self.output_directory, 
                              "default_analysis/nobias_%s.han" % self.subject)
        
        if not os.path.exists(os.path.join(self.output_directory, "default_analysis", "segmentation")):
            os.mkdir(os.path.join(self.output_directory, "default_analysis", "segmentation"))
        self.brain_mask = os.path.join(self.output_directory, 
                          "default_analysis/segmentation/brain_%s.nii" % self.subject)
        self.split_mask = os.path.join(self.output_directory, 
                          "default_analysis/segmentation/voronoi_%s.nii" % self.subject)

    def run_spatial_normalization(self):
        spatial_normalization = SpatialNormalization()

        spatial_normalization.mri = self.mri

        spatial_normalization.commissure_coordinates = self.commissure_coordinates
        spatial_normalization.talairach_transform = self.talairach_transform

        self.assert_(spatial_normalization.run() == 0)


    def run_bias_correction(self):
        bias_correction = BiasCorrection()

        bias_correction.mri = self.mri 
        bias_correction.commissure_coordinates = self.commissure_coordinates
        bias_correction.fix_random_seed = True
        
        bias_correction.hfiltered = self.hfiltered 
        bias_correction.white_ridges = self.white_ridges
        bias_correction.edges = self.edges 
        bias_correction.variance = self.variance 
        bias_correction.mri_corrected = self.mri_corrected 

        self.assert_(bias_correction.run() == 0)
            

    def run_histogram_analysis(self):
        histo_analysis = HistogramAnalysis()
        
        histo_analysis.mri_corrected = self.mri_corrected 
        histo_analysis.white_ridges = self.white_ridges 
        histo_analysis.hfiltered = self.hfiltered
        histo_analysis.fix_random_seed = True

        histo_analysis.histo_analysis = self.histo_analysis
    
        self.assert_(histo_analysis.run() == 0)
    
    
    def run_brain_segmentation(self):
        brain_segmentation = BrainSegmentation()
    
        brain_segmentation.mri_corrected = self.mri_corrected
        brain_segmentation.commissure_coordinates = self.commissure_coordinates
        brain_segmentation.white_ridges = self.white_ridges
        brain_segmentation.edges = self.edges 
        brain_segmentation.variance = self.variance
        brain_segmentation.histo_analysis = self.histo_analysis
        brain_segmentation.fix_random_seed = True

        brain_segmentation.brain_mask = self.brain_mask
    
        self.assert_(brain_segmentation.run() == 0)


    def run_split_brain(self):
        split_brain = SplitBrain()

        split_brain.mri_corrected = self.mri_corrected
        split_brain.brain_mask = self.brain_mask
        split_brain.white_ridges = self.white_ridges
        split_brain.histo_analysis = self.histo_analysis
        split_brain.commissure_coordinates = self.commissure_coordinates
        split_brain.fix_random_seed = True

        split_brain.split_mask = self.split_mask

        self.assert_(split_brain.run() == 0)
        
        
    def test_steps(self):
        self.run_spatial_normalization()
        self.run_bias_correction()
        self.run_histogram_analysis()
        self.run_brain_segmentation()
        self.run_split_brain()
        
        for test_result in [self.hfiltered, self.edges, self.variance, self.mri_corrected, self.white_ridges,
                            self.histo_analysis, self.brain_mask, self.split_mask]:
            ref_result = os.path.join(self.base_directory, 
                                      os.path.relpath(test_result, self.output_directory))
            self.assert_(comp_files(test_result, ref_result), 
                         "The content of %s in test is different from the reference results" % os.path.basename(test_result))
    

def comp_files(nfc1, nfc2, lgbuf=32*1024):
    """Compare les 2 fichiers et renvoie True seulement s'ils ont un contenu 
    identique"""
    f1 = f2 = None
    result = False
    try:
        if os.path.getsize(nfc1) == os.path.getsize(nfc2):
            f1 = open(nfc1, "rb")
            f2 = open(nfc2, "rb")
            while True:
                buf1 = f1.read(lgbuf)
                if len(buf1) == 0:
                    result = True
                    break
                buf2 = f2.read(lgbuf)
                if buf1 != buf2:
                    break
    finally:
        if f1 != None: f1.close()
        if f2 != None: f2.close()
    return result


if __name__ == '__main__':

    unittest.main()

    #tests = []
    #tests.append('test_spatial_normalization')
    ##tests.append('test_bias_correction')
    ##tests.append('test_histogram_analysis')
    ##tests.append('test_brain_segmentation')
    ##tests.append('test_split_brain')

    #test_suite = unittest.TestSuite(map(TestIntraAnalysisSteps, tests))
    #unittest.TextTestRunner(verbosity=2).run(test_suite)
