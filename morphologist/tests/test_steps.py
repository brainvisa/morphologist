import os
import unittest
import shutil

from morphologist.steps import SpatialNormalization, BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain

import brainvisa.axon
from brainvisa.processes import defaultContext
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy

class TestIntraAnalysisSteps(unittest.TestCase):
    
    def create_ref_database(self):
        if not os.path.exists(self.bv_db_directory):
            os.makedirs( self.bv_db_directory )
            brainvisa.axon.initializeProcesses()
            database_settings = neuroConfig.DatabaseSettings( self.bv_db_directory )
            database = neuroHierarchy.SQLDatabase( os.path.join(self.bv_db_directory, "database.sqlite"), 
                                                   self.bv_db_directory, 
                                                   'brainvisa-3.1.0', 
                                                   context=defaultContext(), 
                                                   settings=database_settings )
            neuroHierarchy.databases.add( database )
            neuroConfig.dataPath.append( database_settings )
            input = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/%s.nii" % self.subject
            t1mri = {"_database" : database.name, '_format' : 'NIFTI-1 image', 
                         "protocol" : "test", "subject" : self.subject}
            defaultContext().runProcess('ImportT1MRI', input, t1mri)

            pipeline=brainvisa.processes.getProcessInstance("morphologist")
            nodes=pipeline.executionNode()
            ac = [124.010253906, 110.013366699, 74.0999832153]
            pc = [124.383506775, 136.140884399, 75.3999862671]
            ip = [123.263755798, 102.175109863, 26.0]
            # select steps until split brain and fix the random seed
            nodes.child('TalairachTransformation').setSelected(0)
            nodes.child('GreyWhiteClassification').setSelected(0)
            nodes.child('GreyWhiteSurface').setSelected(0)
            nodes.child('HemispheresMesh').setSelected(0)
            nodes.child('HeadMesh').setSelected(0)
            nodes.child('CorticalFoldsGraph').setSelected(0)
            nodes.child('BiasCorrection').fix_random_seed = True
            nodes.child('HistoAnalysis').fix_random_seed = True
            nodes.child('BrainSegmentation').fix_random_seed = True
            nodes.child('SplitBrain').fix_random_seed = True
    
            print "* Run Axon Morphologist to get reference results"
            defaultContext().runProcess(pipeline, t1mri, Anterior_Commissure=ac, 
                                  Posterior_Commissure=pc, Interhemispheric_Point=ip)
            
            brainvisa.axon.cleanup()

        
    def setUp(self):      
        self.subject = "hyperion"
        self.bv_db_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database"
        self.base_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/test/%s/t1mri/default_acquisition" % self.subject
        self.output_directory = "/tmp/morphologist_test_steps"
        
        self.create_ref_database()
        
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
        
        for (dirpath, dirnames, filenames) in os.walk(self.output_directory):
            for f in filenames:
                f_test = os.path.join(dirpath, f)
                f_ref = os.path.join(self.base_directory, os.path.relpath(dirpath, self.output_directory), f)
                if f.endswith(".minf"):
                    minf_test = eval(open(f_test).read()[13:])
                    minf_ref = eval(open(f_ref).read()[13:])
                    attributes = set(minf_ref.keys())
                    if "uuid" in attributes:
                        attributes.remove("uuid")
                    if "referential" in attributes:
                        attributes.remove("referential")
                    for att in attributes:
                        self.assert_(minf_test.get(att) == minf_ref[att], 
                                     "The content of %s in test is different from the reference results\
for the attribute %s.The reference value is %s, whereas the test value is %s."
                                     % (f, att, str(minf_ref.get(att)), str(minf_test.get(att))))
                else:
                    f_test = os.path.join(dirpath, f)
                    f_ref = os.path.join(self.base_directory, os.path.relpath(dirpath, self.output_directory), f)
                    self.assertTrue(comp_files(f_ref, f_test), 
                                    "The content of "+f+" in test is different from the reference results.")

    

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
