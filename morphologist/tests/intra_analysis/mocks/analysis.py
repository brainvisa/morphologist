import shutil

from morphologist.core.subject import Subject
from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis.parameters import BrainvisaIntraAnalysisParameterTemplate, \
                                                    IntraAnalysisParameterNames    
from morphologist.tests.intra_analysis.mocks.steps import MockSpatialNormalization, \
    MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain, \
    MockGreyWhite, MockGrey, MockGreySurface, MockWhiteSurface, MockSulci, MockSulciLabelling


class MockIntraAnalysis(IntraAnalysis):

    def __init__(self, parameter_template):
        super(MockIntraAnalysis, self).__init__(parameter_template)

    def _init_steps(self):
        subject=Subject("hyperion", "test", None)
        bv_database_directory = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database"
        bv_param_template = BrainvisaIntraAnalysisParameterTemplate(bv_database_directory)
        ref_results = bv_param_template.get_outputs(subject)
        self._normalization = MockSpatialNormalization(ref_results[IntraAnalysisParameterNames.COMMISSURE_COORDINATES], 
                                                       ref_results[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION])
        self._bias_correction = MockBiasCorrection(\
            ref_results[IntraAnalysisParameterNames.HFILTERED],
            ref_results[IntraAnalysisParameterNames.WHITE_RIDGES],
            ref_results[IntraAnalysisParameterNames.EDGES],
            ref_results[IntraAnalysisParameterNames.CORRECTED_MRI],
            ref_results[IntraAnalysisParameterNames.VARIANCE])
        self._histogram_analysis = MockHistogramAnalysis(\
            ref_results[IntraAnalysisParameterNames.HISTO_ANALYSIS],
            ref_results[IntraAnalysisParameterNames.HISTOGRAM])
        self._brain_segmentation = MockBrainSegmentation(\
            ref_results[IntraAnalysisParameterNames.BRAIN_MASK],
            ref_results[IntraAnalysisParameterNames.REFINED_WHITE_RIDGES])
        self._split_brain = MockSplitBrain(\
            ref_results[IntraAnalysisParameterNames.SPLIT_MASK])
        self._left_grey_white = MockGreyWhite(\
            ref_results[IntraAnalysisParameterNames.LEFT_GREY_WHITE])  
        self._right_grey_white = MockGreyWhite(\
            ref_results[IntraAnalysisParameterNames.RIGHT_GREY_WHITE])  
        self._left_grey = MockGrey(ref_results[IntraAnalysisParameterNames.LEFT_GREY])
        self._right_grey = MockGrey(ref_results[IntraAnalysisParameterNames.RIGHT_GREY])
        self._left_grey_surface = MockGreySurface(\
            ref_results[IntraAnalysisParameterNames.LEFT_GREY_SURFACE])
        self._right_grey_surface = MockGreySurface(\
            ref_results[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE])
        self._left_white_surface = MockWhiteSurface(\
            ref_results[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE])
        self._right_white_surface = MockWhiteSurface(\
            ref_results[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE])
        self._left_sulci = MockSulci(\
            ref_results[IntraAnalysisParameterNames.LEFT_SULCI],
            ref_results[IntraAnalysisParameterNames.LEFT_SULCI_DATA])
        self._right_sulci = MockSulci(\
            ref_results[IntraAnalysisParameterNames.RIGHT_SULCI],
            ref_results[IntraAnalysisParameterNames.RIGHT_SULCI_DATA])
        self._left_sulci_labelling = MockSulciLabelling(\
            ref_results[IntraAnalysisParameterNames.LEFT_LABELED_SULCI],
            ref_results[IntraAnalysisParameterNames.LEFT_LABELED_SULCI_DATA])
        self._right_sulci_labelling = MockSulciLabelling(\
            ref_results[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI],
            ref_results[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI_DATA])
        self._steps = [self._normalization, 
                       self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain,
                       self._left_grey_white,
                       self._right_grey_white, 
                       self._left_grey, 
                       self._right_grey,
                       self._left_grey_surface,
                       self._right_grey_surface,
                       self._left_white_surface, 
                       self._right_white_surface,
                       self._left_sulci,
                       self._right_sulci,
                       self._left_sulci_labelling,
                       self._right_sulci_labelling]

    def import_data(self, subject):
        target_filename = self.parameter_template.get_subject_filename(subject)
        self.parameter_template.create_outputdirs(subject)
        source_filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"
        shutil.copy(source_filename, target_filename)
        return target_filename
