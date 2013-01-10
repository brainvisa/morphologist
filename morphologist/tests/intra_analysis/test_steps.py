import os
import unittest
import shutil
import filecmp 
import optparse
import sys

import brainvisa.axon
from brainvisa.processes import defaultContext
from brainvisa.configuration import neuroConfig
from brainvisa.data import neuroHierarchy

from morphologist.intra_analysis_steps import ImageImportation, \
    SpatialNormalization, BiasCorrection, HistogramAnalysis, BrainSegmentation,\
    SplitBrain, LeftGreyWhite, RightGreyWhite, Grey, WhiteSurface
    


class TestIntraAnalysisSteps(unittest.TestCase):
    
    def setUp(self):
        self.subject = "hyperion"
        self.bv_db_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database"
        self.base_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/test/%s/t1mri/default_acquisition" % self.subject
        self.output_directory = "/tmp/morphologist_test_steps"
        self.raw_mri_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/"
        
        if os.path.exists(self.output_directory):
            shutil.rmtree(self.output_directory)
        os.makedirs(self.output_directory)
  
        self.mri = "%s.nii" % self.subject  
        self.commissure_coordinates = "%s.APC" % self.subject 
        
        if not os.path.exists(os.path.join(self.output_directory, "registration")):
            os.mkdir(os.path.join(self.output_directory, "registration"))

        self.talairach_transformation = os.path.join("registration", 
                                                "RawT1-%s_default_acquisition_TO_Talairach-ACPC.trm" 
                                                % self.subject)
        
        if not os.path.exists(os.path.join(self.output_directory, "default_analysis")):
            os.mkdir(os.path.join(self.output_directory, "default_analysis"))
            
        self.hfiltered = os.path.join("default_analysis", "hfiltered_%s.nii" % self.subject)
        self.white_ridges = os.path.join("default_analysis", "whiteridge_%s.nii" % self.subject)
        self.white_ridges_bc = os.path.join("default_analysis", "whiteridge_%s_bc.nii" % self.subject)
        self.edges = os.path.join("default_analysis", "edges_%s.nii" % self.subject)
        self.corrected_mri = os.path.join("default_analysis", "nobias_%s.nii" % self.subject)
        self.variance = os.path.join("default_analysis", "variance_%s.nii" % self.subject)
        self.histo_analysis = os.path.join("default_analysis", "nobias_%s.han" % self.subject)
        
        if not os.path.exists(os.path.join(self.output_directory, "default_analysis", "segmentation")):
            os.mkdir(os.path.join(self.output_directory, "default_analysis", "segmentation"))
        self.brain_mask = os.path.join("default_analysis", "segmentation", "brain_%s.nii" % self.subject)
        self.split_mask = os.path.join("default_analysis", "segmentation", "voronoi_%s.nii" % self.subject)
        self.left_grey_white = os.path.join("default_analysis", "segmentation", 
                                            "Lgrey_white_%s.nii" % self.subject)
        self.right_grey_white = os.path.join("default_analysis", "segmentation", 
                                             "Rgrey_white_%s.nii" % self.subject)
        self.left_grey = os.path.join("default_analysis", "segmentation", "Lcortex_%s.nii" % self.subject)
        self.right_grey = os.path.join("default_analysis", "segmentation", "Rcortex_%s.nii" % self.subject)
        
        if not os.path.exists(os.path.join(self.output_directory, "default_analysis", 
                                           "segmentation", "mesh")):
            os.mkdir(os.path.join(self.output_directory, "default_analysis", 
                                  "segmentation", "mesh"))
        self.left_white_surface = os.path.join("default_analysis", "segmentation", 
                                               "mesh", "%s_Lwhite.gii" % self.subject)
        self.right_white_surface = os.path.join("default_analysis", "segmentation", 
                                                "mesh", "%s_Rwhite.gii" % self.subject)
        
        if not os.path.exists(self.bv_db_directory):
            self._create_ref_database()

    def _create_ref_database(self):
        os.makedirs(self.bv_db_directory)
        brainvisa.axon.initializeProcesses()
        database_settings = neuroConfig.DatabaseSettings(self.bv_db_directory)
        database = neuroHierarchy.SQLDatabase(os.path.join(self.bv_db_directory, "database-2.1.sqlite"), 
                                               self.bv_db_directory, 
                                               'brainvisa-3.1.0', 
                                               context=defaultContext(), 
                                               settings=database_settings )
        neuroHierarchy.databases.add(database)
        raw_mri = os.path.join(self.raw_mri_directory, self.mri)
        t1mri = {"_database" : database.name, '_format' : 'NIFTI-1 image', 
                     "protocol" : "test", "subject" : self.subject}
        defaultContext().runProcess('ImportT1MRI', raw_mri, t1mri)

        pipeline=brainvisa.processes.getProcessInstance("morphologist")
        pipeline.perform_normalization = True
        nodes=pipeline.executionNode()
        # select steps until Grey/White surface and fix the random seed
        nodes.child('TalairachTransformation').setSelected(0)
        nodes.child('HemispheresMesh').setSelected(0)
        nodes.child('HeadMesh').setSelected(0)
        nodes.child('CorticalFoldsGraph').setSelected(0)
        
        nodes.child('BiasCorrection').fix_random_seed = True
        nodes.child('HistoAnalysis').fix_random_seed = True
        nodes.child('BrainSegmentation').fix_random_seed = True
        nodes.child('SplitBrain').fix_random_seed = True
        nodes.child('GreyWhiteClassification').fix_random_seed = True
        nodes.child('GreyWhiteSurface').fix_random_seed = True
        
        print "* Run Axon Morphologist to get reference results"
        print "* First until the bias correction to save the first white ridge result"
        nodes.child('HistoAnalysis').setSelected(0)
        nodes.child('BrainSegmentation').setSelected(0)
        nodes.child('SplitBrain').setSelected(0)
        nodes.child('GreyWhiteClassification').setSelected(0)
        nodes.child('GreyWhiteSurface').setSelected(0)
        defaultContext().runProcess(pipeline, t1mri)
        # Save the white ridge in another file because it will be re-written
        shutil.copy(os.path.join(self.base_directory, self.white_ridges), 
                    os.path.join(self.base_directory, self.white_ridges_bc))
        shutil.copy(os.path.join(self.base_directory, self.white_ridges+".minf"), 
                    os.path.join(self.base_directory, self.white_ridges_bc+".minf"))
        
        print "* Then until Grey/White surface"
        nodes.child('PrepareSubject').setSelected(0)
        nodes.child('BiasCorrection').setSelected(0)
        nodes.child('HistoAnalysis').setSelected(1)
        nodes.child('BrainSegmentation').setSelected(1)
        nodes.child('SplitBrain').setSelected(1)
        nodes.child('GreyWhiteClassification').setSelected(1)
        nodes.child('GreyWhiteSurface').setSelected(1)
        defaultContext().runProcess(pipeline, t1mri)
        
        brainvisa.axon.cleanup()

    def test_image_importation(self):
        image_importation = ImageImportation()
        image_importation.input = os.path.join(self.raw_mri_directory, self.mri)
        image_importation.output = os.path.join(self.output_directory, self.mri)
        self.assert_(image_importation.run() == 0)
        self.compare_results([self.mri])

    def test_spatial_normalization(self):
        spatial_normalization = SpatialNormalization()

        spatial_normalization.mri = os.path.join(self.base_directory, self.mri)

        spatial_normalization.commissure_coordinates = os.path.join(self.output_directory,
                                                                    self.commissure_coordinates)
        spatial_normalization.talairach_transformation = os.path.join(self.output_directory,
                                                                 self.talairach_transformation)
        self.assert_(spatial_normalization.run() == 0)
        self.compare_results([self.commissure_coordinates, self.talairach_transformation])

    def test_bias_correction(self):
        bias_correction = BiasCorrection()

        bias_correction.mri = os.path.join(self.base_directory, self.mri)
        bias_correction.commissure_coordinates = os.path.join(self.base_directory, 
                                                              self.commissure_coordinates)
        bias_correction.fix_random_seed = True
        
        bias_correction.hfiltered = os.path.join(self.output_directory, self.hfiltered) 
        bias_correction.white_ridges = os.path.join(self.output_directory, self.white_ridges_bc)
        bias_correction.edges = os.path.join(self.output_directory, self.edges) 
        bias_correction.variance = os.path.join(self.output_directory, self.variance) 
        bias_correction.corrected_mri = os.path.join(self.output_directory, self.corrected_mri) 
        self.assert_(bias_correction.run() == 0)
        self.compare_results([self.hfiltered, self.white_ridges_bc, self.edges, 
                              self.variance, self.corrected_mri])
        
    def test_histogram_analysis(self):
        histo_analysis = HistogramAnalysis()
        histo_analysis.corrected_mri = os.path.join(self.base_directory, self.corrected_mri)
        histo_analysis.white_ridges = os.path.join(self.base_directory, self.white_ridges_bc)
        histo_analysis.hfiltered = os.path.join(self.base_directory, self.hfiltered)
        histo_analysis.fix_random_seed = True
        histo_analysis.histo_analysis = os.path.join(self.output_directory, self.histo_analysis)
        self.assert_(histo_analysis.run() == 0)
        self.compare_results([self.histo_analysis, self.histo_analysis.replace(".han", ".his")])
        
    def test_brain_segmentation(self):
        brain_segmentation = BrainSegmentation()
        brain_segmentation.corrected_mri = os.path.join(self.base_directory, self.corrected_mri)
        brain_segmentation.commissure_coordinates = os.path.join(self.base_directory, 
                                                                 self.commissure_coordinates)
        brain_segmentation.edges = os.path.join(self.base_directory, self.edges)
        brain_segmentation.variance = os.path.join(self.base_directory, self.variance)
        brain_segmentation.histo_analysis = os.path.join(self.base_directory, self.histo_analysis)
        brain_segmentation.fix_random_seed = True
        brain_segmentation.brain_mask = os.path.join(self.output_directory, self.brain_mask)
        brain_segmentation.white_ridges = os.path.join(self.output_directory, self.white_ridges)
        # copy white ridge file into the output directory because it is an input/output
        shutil.copy(os.path.join(self.base_directory, self.white_ridges_bc), 
                    brain_segmentation.white_ridges)
        shutil.copy(os.path.join(self.base_directory, self.white_ridges_bc+".minf"), 
                    brain_segmentation.white_ridges+".minf")
        self.assert_(brain_segmentation.run() == 0)
        self.compare_results([self.brain_mask, self.white_ridges])

    def test_split_brain(self):
        split_brain = SplitBrain()

        split_brain.corrected_mri = os.path.join(self.base_directory, self.corrected_mri)
        split_brain.brain_mask = os.path.join(self.base_directory, self.brain_mask)
        split_brain.histo_analysis = os.path.join(self.base_directory, self.histo_analysis)
        split_brain.commissure_coordinates = os.path.join(self.base_directory, self.commissure_coordinates)
        split_brain.white_ridges = os.path.join(self.base_directory, self.white_ridges)
        split_brain.fix_random_seed = True
        split_brain.split_mask = os.path.join(self.output_directory, self.split_mask)
        self.assert_(split_brain.run() == 0)
        self.compare_results([self.split_mask])

    def test_grey_white(self):
        left_grey_white = LeftGreyWhite()
        right_grey_white = RightGreyWhite()
        self._init_test_grey_white(left_grey_white)
        self._init_test_grey_white(right_grey_white)

        left_grey_white.left_grey_white = os.path.join(self.output_directory, self.left_grey_white)
        right_grey_white.right_grey_white = os.path.join(self.output_directory, self.right_grey_white)
                
        self.assert_(left_grey_white.run() == 0)
        self.assert_(right_grey_white.run() == 0)
        
        self.compare_results([self.left_grey_white, self.right_grey_white])

    def _init_test_grey_white(self, step):
        step.corrected_mri = os.path.join(self.base_directory, self.corrected_mri)
        step.commissure_coordinates = os.path.join(self.base_directory, self.commissure_coordinates)
        step.histo_analysis = os.path.join(self.base_directory, self.histo_analysis)
        step.split_mask = os.path.join(self.base_directory, self.split_mask)
        step.edges = os.path.join(self.base_directory, self.edges)
        step.fix_random_seed = True
       
    def test_grey(self):
        left_grey = Grey()
        right_grey = Grey()
        self._init_test_grey(left_grey)
        self._init_test_grey(right_grey)

        left_grey.grey_white = os.path.join(self.base_directory, self.left_grey_white)
        left_grey.grey = os.path.join(self.output_directory, self.left_grey)
        right_grey.grey_white = os.path.join(self.base_directory, self.right_grey_white)
        right_grey.grey = os.path.join(self.output_directory, self.right_grey)
                
        self.assert_(left_grey.run() == 0)
        self.assert_(right_grey.run() == 0)
        
        self.compare_results([self.left_grey, self.right_grey])
       
    def _init_test_grey(self, step):
        step.corrected_mri = os.path.join(self.base_directory, self.corrected_mri)
        step.histo_analysis = os.path.join(self.base_directory, self.histo_analysis)
        step.fix_random_seed = True
        
    def test_white_surface(self):
        left_white_surface = WhiteSurface()
        right_white_surface = WhiteSurface()
        
        left_white_surface.grey = os.path.join(self.base_directory, self.left_grey)
        right_white_surface.grey = os.path.join(self.base_directory, self.right_grey)
        left_white_surface.white_mesh = os.path.join(self.output_directory, self.left_white_surface)
        right_white_surface.white_mesh = os.path.join(self.output_directory, self.right_white_surface)
        
        self.assert_(left_white_surface.run() == 0)
        self.assert_(right_white_surface.run() == 0)
        
        self.compare_results([self.left_white_surface, self.right_white_surface])
  
    def compare_results(self, results):
        for f in results:
            f_ref = os.path.join(self.base_directory, f)
            f_test = os.path.join(self.output_directory, f)
            self.assert_(filecmp.cmp(f_ref, f_test), 
                         "The content of %s in test is different from the reference results." 
                         % os.path.basename(f))
            self.compare_minf(f_ref+".minf", f_test+".minf")

    def compare_minf(self, f_minf_ref, f_minf_test):
        # The minf files are not always written the same way 
        # but the value of the common attributes should be the same
        if not os.path.exists(f_minf_ref):
            self.assertFalse(os.path.exists(f_minf_test))
        elif os.path.exists(f_minf_test):
            minf_test = eval(open(f_minf_test).read()[13:])
            minf_ref = eval(open(f_minf_ref).read()[13:])
            attributes_ref = set(minf_ref.keys())
            if "uuid" in attributes_ref:
                attributes_ref.remove("uuid")
            if "referential" in attributes_ref:
                attributes_ref.remove("referential")
            attributes_test = set(minf_test.keys())
            difference = attributes_ref.difference(attributes_test)
            self.assert_(difference == set(),
                         "The content of %s in test is different from the reference results. \
Some attributes are not the same: %s." % (os.path.basename(f_minf_ref), str(difference)) )
            for att in attributes_ref:
                self.assert_(minf_test.get(att) == minf_ref[att], 
                             "The content of %s in test is different from the reference results \
for the attribute %s. The reference value is %s, whereas the test value is %s."
% (os.path.basename(f_minf_ref), att, str(minf_ref.get(att)), str(minf_test.get(att)) ) )


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-t', '--test', 
                      dest="test", default=None, 
                      help="Execute only this test function.")
    options, _ = parser.parse_args(sys.argv)
    if options.test is None:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        test_suite = unittest.TestSuite([TestIntraAnalysisSteps(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
