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
    SplitBrain, GreyWhite, Grey, WhiteSurface
from morphologist.intra_analysis import BrainvisaIntraAnalysisParameterTemplate, \
                                        IntraAnalysis    


class TestIntraAnalysisSteps(unittest.TestCase):
    
    def setUp(self):
        self.subject = "hyperion"
        self.group = "test"
        self.bv_db_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database"
        self.output_directory = "/tmp/morphologist_test_steps"
        self.raw_mri = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/%s.nii" % self.subject
        
        if os.path.exists(self.output_directory):
            shutil.rmtree(self.output_directory)
        os.makedirs(self.output_directory)
  
        self.ref_outputs = BrainvisaIntraAnalysisParameterTemplate.get_outputs(self.group, 
                                                                    self.subject, self.bv_db_directory)
        self.test_outputs = BrainvisaIntraAnalysisParameterTemplate.get_outputs(self.group, 
                                                                  self.subject, self.output_directory)
        
        self.ref_white_ridges_bc = self.ref_outputs[IntraAnalysis.WHITE_RIDGES].replace(".nii", "_bc.nii")
        self.test_white_ridges_bc = self.test_outputs[IntraAnalysis.WHITE_RIDGES].replace(".nii", "_bc.nii")
        
        BrainvisaIntraAnalysisParameterTemplate.create_outputdirs(self.group, self.subject, 
                                                                  self.output_directory)
        self.ref_mri = BrainvisaIntraAnalysisParameterTemplate.get_mri_path(self.group, 
                                                    self.subject, self.bv_db_directory)
        self.test_mri = BrainvisaIntraAnalysisParameterTemplate.get_mri_path(self.group, 
                                                    self.subject, self.output_directory)
        
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
        t1mri = {"_database" : database.name, '_format' : 'NIFTI-1 image', 
                "protocol" : self.group, "subject" : self.subject}
        defaultContext().runProcess('ImportT1MRI', self.raw_mri, t1mri)

        pipeline=brainvisa.processes.getProcessInstance("morphologist")
        pipeline.perform_normalization = True
        nodes=pipeline.executionNode()
        # select steps until Grey/White surface and fix the random seed
        nodes.child('TalairachTransformation').setSelected(0)
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
        nodes.child('HemispheresMesh').setSelected(0)
        defaultContext().runProcess(pipeline, t1mri)
        # Save the white ridge in another file because it will be re-written
        white_ridges = self.ref_outputs[IntraAnalysis.WHITE_RIDGES]
        shutil.copy(white_ridges, self.ref_white_ridges_bc) 
        shutil.copy(white_ridges+".minf", self.ref_white_ridges_bc+".minf")
        
        print "* Then until Grey/White surface"
        nodes.child('PrepareSubject').setSelected(0)
        nodes.child('BiasCorrection').setSelected(0)
        nodes.child('HistoAnalysis').setSelected(1)
        nodes.child('BrainSegmentation').setSelected(1)
        nodes.child('SplitBrain').setSelected(1)
        nodes.child('GreyWhiteClassification').setSelected(1)
        nodes.child('GreyWhiteSurface').setSelected(1)
        nodes.child('HemispheresMesh').setSelected(1)
        defaultContext().runProcess(pipeline, t1mri)

        brainvisa.axon.cleanup()

    def test_image_importation(self):
        image_importation = ImageImportation()
        image_importation.input = self.raw_mri
        image_importation.output = self.test_mri
        self.assert_(image_importation.run() == 0)
        self._assert_same_files(self.ref_mri, self.test_mri)

    def test_spatial_normalization(self):
        normalization = SpatialNormalization()

        normalization.mri = self.ref_mri

        normalization.commissure_coordinates = self.test_outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        normalization.talairach_transformation = self.test_outputs[IntraAnalysis.TALAIRACH_TRANSFORMATION]
        self.assert_(normalization.run() == 0)
        self._assert_same_results([IntraAnalysis.COMMISSURE_COORDINATES, IntraAnalysis.TALAIRACH_TRANSFORMATION])

    def test_bias_correction(self):
        bias_correction = BiasCorrection()

        bias_correction.mri = self.ref_mri
        bias_correction.commissure_coordinates = self.ref_outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        bias_correction.fix_random_seed = True
        
        bias_correction.hfiltered = self.test_outputs[IntraAnalysis.HFILTERED] 
        bias_correction.white_ridges = self.test_white_ridges_bc
        bias_correction.edges = self.test_outputs[IntraAnalysis.EDGES] 
        bias_correction.variance = self.test_outputs[IntraAnalysis.VARIANCE]  
        bias_correction.corrected_mri = self.test_outputs[IntraAnalysis.CORRECTED_MRI]  
        self.assert_(bias_correction.run() == 0)
        self._assert_same_results([IntraAnalysis.HFILTERED, IntraAnalysis.EDGES, 
                              IntraAnalysis.VARIANCE, IntraAnalysis.CORRECTED_MRI])
        self._assert_same_files(self.ref_white_ridges_bc, self.test_white_ridges_bc)
        
    def test_histogram_analysis(self):
        histo_analysis = HistogramAnalysis()
        histo_analysis.corrected_mri = self.ref_outputs[IntraAnalysis.CORRECTED_MRI]
        histo_analysis.white_ridges = self.ref_white_ridges_bc
        histo_analysis.hfiltered = self.ref_outputs[IntraAnalysis.HFILTERED]
        histo_analysis.fix_random_seed = True
        histo_analysis.histo_analysis = self.test_outputs[IntraAnalysis.HISTO_ANALYSIS]
        histo_analysis.histogram = self.test_outputs[IntraAnalysis.HISTOGRAM]
        self.assert_(histo_analysis.run() == 0)
        self._assert_same_results([IntraAnalysis.HISTO_ANALYSIS,
                                   IntraAnalysis.HISTOGRAM])
        
    def test_brain_segmentation(self):
        brain_segmentation = BrainSegmentation()
        brain_segmentation.corrected_mri = self.ref_outputs[IntraAnalysis.CORRECTED_MRI]
        brain_segmentation.commissure_coordinates = self.ref_outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        brain_segmentation.edges = self.ref_outputs[IntraAnalysis.EDGES]
        brain_segmentation.variance = self.ref_outputs[IntraAnalysis.VARIANCE]
        brain_segmentation.histo_analysis = self.ref_outputs[IntraAnalysis.HISTO_ANALYSIS]
        brain_segmentation.fix_random_seed = True
        brain_segmentation.brain_mask = self.test_outputs[IntraAnalysis.BRAIN_MASK]
        brain_segmentation.white_ridges = self.test_outputs[IntraAnalysis.WHITE_RIDGES]
        # copy white ridge file into the output directory because it is an input/output
        shutil.copy(self.ref_white_ridges_bc, brain_segmentation.white_ridges)
        shutil.copy(self.ref_white_ridges_bc+".minf", 
                    brain_segmentation.white_ridges+".minf")
        self.assert_(brain_segmentation.run() == 0)
        self._assert_same_results([IntraAnalysis.BRAIN_MASK, IntraAnalysis.WHITE_RIDGES])

    def test_split_brain(self):
        split_brain = SplitBrain()

        split_brain.corrected_mri = self.ref_outputs[IntraAnalysis.CORRECTED_MRI]
        split_brain.brain_mask = self.ref_outputs[IntraAnalysis.BRAIN_MASK]
        split_brain.histo_analysis = self.ref_outputs[IntraAnalysis.HISTO_ANALYSIS]
        split_brain.commissure_coordinates = self.ref_outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        split_brain.white_ridges = self.ref_outputs[IntraAnalysis.WHITE_RIDGES]
        split_brain.fix_random_seed = True
        split_brain.split_mask = self.test_outputs[IntraAnalysis.SPLIT_MASK]
        self.assert_(split_brain.run() == 0)
        self._assert_same_results([IntraAnalysis.SPLIT_MASK])

    def test_grey_white(self):
        left_grey_white = GreyWhite(left=True)
        right_grey_white = GreyWhite(left=False)
        self._init_test_grey_white(left_grey_white)
        self._init_test_grey_white(right_grey_white)

        left_grey_white.grey_white = self.test_outputs[IntraAnalysis.LEFT_GREY_WHITE]
        right_grey_white.grey_white = self.test_outputs[IntraAnalysis.RIGHT_GREY_WHITE]
                
        self.assert_(left_grey_white.run() == 0)
        self.assert_(right_grey_white.run() == 0)
        
        self._assert_same_results([IntraAnalysis.LEFT_GREY_WHITE, IntraAnalysis.RIGHT_GREY_WHITE])

    def _init_test_grey_white(self, step):
        step.corrected_mri = self.ref_outputs[IntraAnalysis.CORRECTED_MRI]
        step.commissure_coordinates = self.ref_outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        step.histo_analysis = self.ref_outputs[IntraAnalysis.HISTO_ANALYSIS]
        step.split_mask = self.ref_outputs[IntraAnalysis.SPLIT_MASK]
        step.edges = self.ref_outputs[IntraAnalysis.EDGES]
        step.fix_random_seed = True
       
    def test_grey(self):
        left_grey = Grey()
        right_grey = Grey()
        self._init_test_grey(left_grey)
        self._init_test_grey(right_grey)

        left_grey.grey_white = self.ref_outputs[IntraAnalysis.LEFT_GREY_WHITE]
        left_grey.grey = self.test_outputs[IntraAnalysis.LEFT_GREY]
        right_grey.grey_white = self.ref_outputs[IntraAnalysis.RIGHT_GREY_WHITE]
        right_grey.grey = self.test_outputs[IntraAnalysis.RIGHT_GREY]
                
        self.assert_(left_grey.run() == 0)
        self.assert_(right_grey.run() == 0)
        
        self._assert_same_results([IntraAnalysis.LEFT_GREY, IntraAnalysis.RIGHT_GREY])
       
    def _init_test_grey(self, step):
        step.corrected_mri = self.ref_outputs[IntraAnalysis.CORRECTED_MRI]
        step.histo_analysis = self.ref_outputs[IntraAnalysis.HISTO_ANALYSIS]
        step.fix_random_seed = True
        
    def test_white_surface(self):
        left_white_surface = WhiteSurface()
        right_white_surface = WhiteSurface()
        
        left_white_surface.grey = self.ref_outputs[IntraAnalysis.LEFT_GREY]
        right_white_surface.grey = self.ref_outputs[IntraAnalysis.RIGHT_GREY]
        left_white_surface.white_surface = self.test_outputs[IntraAnalysis.LEFT_WHITE_SURFACE]
        right_white_surface.white_surface = self.test_outputs[IntraAnalysis.RIGHT_WHITE_SURFACE]
        
        self.assert_(left_white_surface.run() == 0)
        self.assert_(right_white_surface.run() == 0)
        
        self._assert_same_results([IntraAnalysis.LEFT_WHITE_SURFACE, IntraAnalysis.RIGHT_WHITE_SURFACE])

    def _assert_same_files(self, file_ref, file_test):
        self.assert_(filecmp.cmp(file_ref, file_test), 
                     "The content of %s in test is different from the reference results." 
                     % os.path.basename(file_ref))
        # the check of minf files is disabled for the moment because we do not use these files
        #self._assert_same_minf_files(file_ref+".minf", file_test+".minf")
        
    def _assert_same_results(self, results):
        for parameter_name in results:
            f_ref = self.ref_outputs[parameter_name]
            f_test = self.test_outputs[parameter_name]
            self._assert_same_files(f_ref, f_test)
            
    def _assert_same_minf_files(self, f_minf_ref, f_minf_test):
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
