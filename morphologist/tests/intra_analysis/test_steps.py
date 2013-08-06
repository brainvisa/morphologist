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

from morphologist.core.subject import Subject
from morphologist.intra_analysis.steps import ImageImportation, \
    SpatialNormalization, BiasCorrection, HistogramAnalysis, BrainSegmentation,\
    #SplitBrain, GreyWhite, Grey, WhiteSurface, GreySurface, Sulci, SulciLabelling
from morphologist.intra_analysis.parameters import BrainvisaIntraAnalysisParameterTemplate, \
                                                    IntraAnalysisParameterNames    
from morphologist.tests.utils.graph_comparison import same_graphs
from morphologist.intra_analysis import constants


class TestIntraAnalysisSteps(unittest.TestCase):
    
    def setUp(self):
        self.subjectname = "hyperion"
        self.groupname = "test"
        self.bv_db_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database"
        self.output_directory = "/tmp/morphologist_test_steps"
        self.raw_mri = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/%s.nii" % self.subjectname
        
        if os.path.exists(self.output_directory):
            shutil.rmtree(self.output_directory)
        os.makedirs(self.output_directory)
  
        subject = Subject(self.subjectname, self.groupname, self.raw_mri)
        ref_param_template = BrainvisaIntraAnalysisParameterTemplate(self.bv_db_directory)
        test_param_template = BrainvisaIntraAnalysisParameterTemplate(self.output_directory)
        self.ref_outputs = ref_param_template.get_outputs(subject)
        self.test_outputs = test_param_template.get_outputs(subject)
        
        test_param_template.create_outputdirs(subject)
        self.ref_mri = ref_param_template.get_subject_filename(subject)
        self.test_mri = test_param_template.get_subject_filename(subject)
        
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
                "protocol" : self.groupname, "subject" : self.subjectname}
        defaultContext().runProcess('ImportT1MRI', self.raw_mri, t1mri)

        pipeline=brainvisa.processes.getProcessInstance("morphologist")
        pipeline.perform_normalization = True
        nodes=pipeline.executionNode()
        # select steps until Grey/White surface and fix the random seed
        nodes.child('TalairachTransformation').setSelected(0)
        nodes.child('HeadMesh').setSelected(0)
        
        nodes.child('BiasCorrection').fix_random_seed = True
        nodes.child('HistoAnalysis').fix_random_seed = True
        nodes.child('BrainSegmentation').fix_random_seed = True
        nodes.child('SplitBrain').fix_random_seed = True
        nodes.child('GreyWhiteClassification').fix_random_seed = True
        nodes.child('GreyWhiteSurface').fix_random_seed = True
        nodes.child('HemispheresMesh').fix_random_seed = True
        nodes.child('CorticalFoldsGraph').fix_random_seed = True
        
        print "* Run Axon Morphologist to get reference results"
        print "* First until the bias correction to save the first white ridge result"
        nodes.child('HistoAnalysis').setSelected(0)
        nodes.child('BrainSegmentation').setSelected(0)
        nodes.child('SplitBrain').setSelected(0)
        nodes.child('GreyWhiteClassification').setSelected(0)
        nodes.child('GreyWhiteSurface').setSelected(0)
        nodes.child('HemispheresMesh').setSelected(0)
        nodes.child('CorticalFoldsGraph').setSelected(0)
        defaultContext().runProcess(pipeline, t1mri)
        # Save the white ridge in another file because it will be re-written
        bv_white_ridges = self.ref_outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        shutil.copy(bv_white_ridges + ".minf", raw_white_ridges + ".minf") 
        
        print "* Then run the rest of the pipeline"
        nodes.child('PrepareSubject').setSelected(0)
        nodes.child('BiasCorrection').setSelected(0)
        nodes.child('HistoAnalysis').setSelected(1)
        nodes.child('BrainSegmentation').setSelected(1)
        nodes.child('SplitBrain').setSelected(1)
        nodes.child('GreyWhiteClassification').setSelected(1)
        nodes.child('GreyWhiteSurface').setSelected(1)
        nodes.child('HemispheresMesh').setSelected(1)
        nodes.child('CorticalFoldsGraph').setSelected(1)
        nodes.child('SulciRecognition').setSelected(1)
        
        defaultContext().runProcess(pipeline, t1mri)

        brainvisa.axon.cleanup()

    def test_image_importation(self):
        image_importation = ImageImportation()
        image_importation.inputs.input = self.raw_mri
        image_importation.outputs.output = self.test_mri
        self.assert_(image_importation.run() == 0)
        self.assert_(self._same_files(self.ref_mri, self.test_mri))

    def test_spatial_normalization(self):
        normalization = SpatialNormalization()

        normalization.inputs.mri = self.ref_mri

        normalization.outputs.commissure_coordinates = self.test_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        normalization.outputs.talairach_transformation = self.test_outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        self.assert_(normalization.run() == 0)
        self._assert_same_results([IntraAnalysisParameterNames.COMMISSURE_COORDINATES, 
                                  IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION],
                                  self._same_files)

    def test_bias_correction(self):
        bias_correction = BiasCorrection()

        bias_correction.inputs.mri = self.ref_mri
        bias_correction.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        bias_correction.inputs.fix_random_seed = True
        
        bias_correction.outputs.hfiltered = self.test_outputs[IntraAnalysisParameterNames.HFILTERED] 
        bias_correction.outputs.white_ridges = self.test_outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        bias_correction.outputs.edges = self.test_outputs[IntraAnalysisParameterNames.EDGES] 
        bias_correction.outputs.variance = self.test_outputs[IntraAnalysisParameterNames.VARIANCE]  
        bias_correction.outputs.corrected_mri = self.test_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]  
        self.assert_(bias_correction.run() == 0)
        self._assert_same_results([IntraAnalysisParameterNames.HFILTERED,
                IntraAnalysisParameterNames.EDGES, IntraAnalysisParameterNames.VARIANCE,
                IntraAnalysisParameterNames.CORRECTED_MRI, IntraAnalysisParameterNames.WHITE_RIDGES],
                self._same_files)
        
    def test_histogram_analysis(self):
        histo_analysis = HistogramAnalysis()
        histo_analysis.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        histo_analysis.inputs.hfiltered = self.ref_outputs[IntraAnalysisParameterNames.HFILTERED]
        histo_analysis.inputs.white_ridges = self.ref_outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        histo_analysis.inputs.fix_random_seed = True
        histo_analysis.outputs.histo_analysis = self.test_outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        histo_analysis.outputs.histogram = self.test_outputs[IntraAnalysisParameterNames.HISTOGRAM]
        self.assert_(histo_analysis.run() == 0)
        self._assert_same_results([IntraAnalysisParameterNames.HISTO_ANALYSIS,
                                   IntraAnalysisParameterNames.HISTOGRAM],
                                   self._same_files)
        
    def test_brain_segmentation(self):
        brain_segmentation = BrainSegmentation()
        brain_segmentation.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        brain_segmentation.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        brain_segmentation.inputs.edges = self.ref_outputs[IntraAnalysisParameterNames.EDGES]
        brain_segmentation.inputs.variance = self.ref_outputs[IntraAnalysisParameterNames.VARIANCE]
        brain_segmentation.inputs.histo_analysis = self.ref_outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        brain_segmentation.inputs.fix_random_seed = True
        brain_segmentation.inputs.white_ridges = self.ref_outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        brain_segmentation.outputs.brain_mask = self.test_outputs[IntraAnalysisParameterNames.BRAIN_MASK]
        self.assert_(brain_segmentation.run() == 0)
        self._assert_same_results([IntraAnalysisParameterNames.BRAIN_MASK],
                                   self._same_files)

    def test_split_brain(self):
        split_brain = SplitBrain()

        split_brain.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        split_brain.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        split_brain.inputs.brain_mask = self.ref_outputs[IntraAnalysisParameterNames.BRAIN_MASK]
        split_brain.inputs.white_ridges = self.ref_outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        split_brain.inputs.histo_analysis = self.ref_outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        split_brain.inputs.fix_random_seed = True
        split_brain.outputs.split_mask = self.test_outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self.assert_(split_brain.run() == 0)
        self._assert_same_results([IntraAnalysisParameterNames.SPLIT_MASK], self._same_files)

    def test_grey_white(self):
        left_grey_white = GreyWhite(constants.LEFT)
        right_grey_white = GreyWhite(constants.RIGHT)
        self._init_test_grey_white(left_grey_white)
        self._init_test_grey_white(right_grey_white)

        left_grey_white.outputs.grey_white = self.test_outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        right_grey_white.outputs.grey_white = self.test_outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
                
        self.assert_(left_grey_white.run() == 0)
        self.assert_(right_grey_white.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_GREY_WHITE, 
                                   IntraAnalysisParameterNames.RIGHT_GREY_WHITE],
                                   self._same_files)

    def _init_test_grey_white(self, step):
        step.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        step.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        step.inputs.histo_analysis = self.ref_outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        step.inputs.split_mask = self.ref_outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        step.inputs.edges = self.ref_outputs[IntraAnalysisParameterNames.EDGES]
        step.inputs.fix_random_seed = True
       
    def test_grey(self):
        left_grey = Grey()
        right_grey = Grey()
        self._init_test_grey(left_grey)
        self._init_test_grey(right_grey)

        left_grey.inputs.grey_white = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        left_grey.outputs.grey = self.test_outputs[IntraAnalysisParameterNames.LEFT_GREY]
        right_grey.inputs.grey_white = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
        right_grey.outputs.grey = self.test_outputs[IntraAnalysisParameterNames.RIGHT_GREY]
                
        self.assert_(left_grey.run() == 0)
        self.assert_(right_grey.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_GREY, 
                                   IntraAnalysisParameterNames.RIGHT_GREY],
                                   self._same_files)
       
    def _init_test_grey(self, step):
        step.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        step.inputs.histo_analysis = self.ref_outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        step.inputs.fix_random_seed = True
        
    def test_white_surface(self):
        left_white_surface = WhiteSurface()
        right_white_surface = WhiteSurface()
        
        left_white_surface.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY]
        right_white_surface.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        left_white_surface.outputs.white_surface = self.test_outputs[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]
        right_white_surface.outputs.white_surface = self.test_outputs[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]
        
        self.assert_(left_white_surface.run() == 0)
        self.assert_(right_white_surface.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_WHITE_SURFACE, 
                                   IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE],
                                   self._same_files)

    def test_grey_surface(self):
        left_grey_surface = GreySurface(constants.LEFT)
        right_grey_surface = GreySurface(constants.RIGHT)
       
        left_grey_surface.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        right_grey_surface.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        left_grey_surface.inputs.split_mask = self.ref_outputs[IntraAnalysisParameterNames.SPLIT_MASK] 
        right_grey_surface.inputs.split_mask = self.ref_outputs[IntraAnalysisParameterNames.SPLIT_MASK] 
        left_grey_surface.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY]
        right_grey_surface.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        left_grey_surface.outputs.grey_surface = self.test_outputs[IntraAnalysisParameterNames.LEFT_GREY_SURFACE]
        right_grey_surface.outputs.grey_surface = self.test_outputs[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE]
        
        self.assert_(left_grey_surface.run() == 0)
        self.assert_(right_grey_surface.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_GREY_SURFACE, 
                                   IntraAnalysisParameterNames.RIGHT_GREY_SURFACE],
                                   self._same_files)

    def test_sulci_left(self):
        left_sulci = Sulci(constants.LEFT)
         
        left_sulci.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        left_sulci.inputs.split_mask = self.ref_outputs[IntraAnalysisParameterNames.SPLIT_MASK] 
        left_sulci.inputs.talairach_transformation = self.ref_outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        left_sulci.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        left_sulci.inputs.grey_white = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        left_sulci.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY]
        left_sulci.inputs.grey_surface = self.ref_outputs[IntraAnalysisParameterNames.LEFT_GREY_SURFACE]
        left_sulci.inputs.white_surface = self.ref_outputs[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]

        left_sulci.outputs.sulci = self.test_outputs[IntraAnalysisParameterNames.LEFT_SULCI]
        
        self.assert_(left_sulci.run() == 0)
       
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_SULCI],
                                  same_graphs) 

    def test_sulci_right(self):
        right_sulci = Sulci(constants.RIGHT)
         
        right_sulci.inputs.corrected_mri = self.ref_outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        right_sulci.inputs.split_mask = self.ref_outputs[IntraAnalysisParameterNames.SPLIT_MASK] 
        right_sulci.inputs.talairach_transformation = self.ref_outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        right_sulci.inputs.commissure_coordinates = self.ref_outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        right_sulci.inputs.grey_white = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
        right_sulci.inputs.grey = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        right_sulci.inputs.grey_surface = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE]
        right_sulci.inputs.white_surface = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]

        right_sulci.outputs.sulci = self.test_outputs[IntraAnalysisParameterNames.RIGHT_SULCI]
        
        self.assert_(right_sulci.run() == 0)
       
        self._assert_same_results([IntraAnalysisParameterNames.RIGHT_SULCI],
                                  same_graphs) 

    def test_sulci_labelling_left(self):
        left_sulci_labelling = SulciLabelling(constants.LEFT)
    
        left_sulci_labelling.inputs.sulci = self.ref_outputs[IntraAnalysisParameterNames.LEFT_SULCI] 
        left_sulci_labelling.outputs.labeled_sulci = self.test_outputs[IntraAnalysisParameterNames.LEFT_LABELED_SULCI] 
        self.assert_(left_sulci_labelling.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.LEFT_LABELED_SULCI],
                                   self._same_graphs) 

    def test_sulci_labelling_right(self):
        right_sulci_labelling = SulciLabelling(constants.RIGHT)
    
        right_sulci_labelling.inputs.sulci = self.ref_outputs[IntraAnalysisParameterNames.RIGHT_SULCI] 
        right_sulci_labelling.outputs.labeled_sulci = self.test_outputs[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI] 
 
        self.assert_(right_sulci_labelling.run() == 0)
        
        self._assert_same_results([IntraAnalysisParameterNames.RIGHT_LABELED_SULCI],
                                   self._same_graphs) 

    def _assert_same_results(self, results, comparison_function):
        for parameter_name in results:
            f_ref = self.ref_outputs[parameter_name]
            f_test = self.test_outputs[parameter_name]
            print "compare \n" + f_ref + "\n" + f_test
            self.assert_(comparison_function(f_ref, f_test),
                         "The result %s is different from the reference result." 
                         % os.path.basename(f_ref))
            # the check of minf files is disabled for the moment because we do not use these files
            #self._assert_same_minf_files(file_ref+".minf", file_test+".minf")

    def _same_files(self, file_ref, file_test):
        return filecmp.cmp(file_ref, file_test) 
            
    def _same_graphs(self, file_ref, file_test):
        return same_graphs(file_ref, file_test, verbose=True)

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
        test_suite = unittest.TestLoader().loadTestsFromTestCase(TestIntraAnalysisSteps)
        unittest.TextTestRunner(verbosity=2).run(test_suite)
    else:
        test_suite = unittest.TestSuite([TestIntraAnalysisSteps(options.test)])
        unittest.TextTestRunner(verbosity=2).run(test_suite)
