from __future__ import absolute_import
import shutil
import os

from morphologist.core.subject import Subject
from morphologist.intra_analysis import IntraAnalysis, constants
from morphologist.intra_analysis.steps import Morphometry
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames
from morphologist.tests.intra_analysis.mocks.steps import MockSpatialNormalization, \
    MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain, \
    MockGreyWhite, MockGrey, MockGreySurface, MockWhiteSurface, MockSulci, MockSulciLabelling 
# CAPSUL
from capsul.pipeline import pipeline_tools


class MockIntraAnalysis(IntraAnalysis):

    def __init__(self, study):
        super(MockIntraAnalysis, self).__init__(study)

    #def import_data(self, subject):
        #target_filename = self.get_subject_filename(subject)

        #from capsul.process import get_process_instance
        #import_step = get_process_instance(
            #'morphologist.capsul.import_t1_mri.ImportT1Mri')

        #import_step.input = subject.filename
        #import_step.output \
            #= self.pipeline.process.t1mri
        #import_step.referential = self.pipeline.process. \
            #PrepareSubject_TalairachFromNormalization_source_referential
        #pipeline_tools.create_output_directories(import_step)

        ##self.parameter_template.create_outputdirs(subject)
        #target_dirname = os.path.dirname(target_filename)
        #if not os.path.isdir(target_dirname):
            #os.makedirs(target_dirname)
        #test_dir = os.getenv("BRAINVISA_TEST_RUN_DATA_DIR")
        #if not test_dir:
            #raise RuntimeError('BRAINVISA_TEST_RUN_DATA_DIR is not set')
        #test_dir = os.path.join(test_dir, 'tmp_tests_brainvisa')
        #source_filename = os.path.join(
            #test_dir,
            #"tmp_tests_brainvisa/data_unprocessed/sujet01/anatomy/sujet01.ima")
        #shutil.copy(source_filename, target_filename)
        #return target_filename
