import shutil

from morphologist.core.subject import Subject
from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis import BrainvisaIntraAnalysisParameterTemplate
from morphologist.tests.intra_analysis.mocks.steps import MockSpatialNormalization, \
    MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain, \
    MockGreyWhite, MockGrey, MockGreySurface, MockWhiteSurface, MockSulci, MockSulciLabelling


class MockIntraAnalysis(IntraAnalysis):

    def __init__(self):
        super(MockIntraAnalysis, self).__init__()

    def _init_steps(self):
        subject=Subject("hyperion", "test", None)
        ref_results = BrainvisaIntraAnalysisParameterTemplate.get_outputs(subject,
                        "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database")
        self._normalization = MockSpatialNormalization(ref_results[IntraAnalysis.COMMISSURE_COORDINATES], ref_results[IntraAnalysis.TALAIRACH_TRANSFORMATION])
        self._bias_correction = MockBiasCorrection(\
            ref_results[IntraAnalysis.HFILTERED],
            ref_results[IntraAnalysis.WHITE_RIDGES],
            ref_results[IntraAnalysis.EDGES],
            ref_results[IntraAnalysis.CORRECTED_MRI],
            ref_results[IntraAnalysis.VARIANCE])
        self._histogram_analysis = MockHistogramAnalysis(\
            ref_results[IntraAnalysis.HISTO_ANALYSIS],
            ref_results[IntraAnalysis.HISTOGRAM])
        self._brain_segmentation = MockBrainSegmentation(\
            ref_results[IntraAnalysis.BRAIN_MASK],
            ref_results[IntraAnalysis.REFINED_WHITE_RIDGES])
        self._split_brain = MockSplitBrain(\
            ref_results[IntraAnalysis.SPLIT_MASK])
        self._left_grey_white = MockGreyWhite(\
            ref_results[IntraAnalysis.LEFT_GREY_WHITE])  
        self._right_grey_white = MockGreyWhite(\
            ref_results[IntraAnalysis.RIGHT_GREY_WHITE])  
        self._left_grey = MockGrey(ref_results[IntraAnalysis.LEFT_GREY])
        self._right_grey = MockGrey(ref_results[IntraAnalysis.RIGHT_GREY])
        self._left_grey_surface = MockGreySurface(\
            ref_results[IntraAnalysis.LEFT_GREY_SURFACE])
        self._right_grey_surface = MockGreySurface(\
            ref_results[IntraAnalysis.RIGHT_GREY_SURFACE])
        self._left_white_surface = MockWhiteSurface(\
            ref_results[IntraAnalysis.LEFT_WHITE_SURFACE])
        self._right_white_surface = MockWhiteSurface(\
            ref_results[IntraAnalysis.RIGHT_WHITE_SURFACE])
        self._left_sulci = MockSulci(\
            ref_results[IntraAnalysis.LEFT_SULCI],
            ref_results[IntraAnalysis.LEFT_SULCI_DATA])
        self._right_sulci = MockSulci(\
            ref_results[IntraAnalysis.RIGHT_SULCI],
            ref_results[IntraAnalysis.RIGHT_SULCI_DATA])
        self._left_sulci_labelling = MockSulciLabelling(\
            ref_results[IntraAnalysis.LEFT_LABELED_SULCI],
            ref_results[IntraAnalysis.LEFT_LABELED_SULCI_DATA])
        self._right_sulci_labelling = MockSulciLabelling(\
            ref_results[IntraAnalysis.RIGHT_LABELED_SULCI],
            ref_results[IntraAnalysis.RIGHT_LABELED_SULCI_DATA])
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

    @classmethod
    def import_data(cls, parameter_template, subject, outputdir):
        target_filename = cls.get_mri_path(parameter_template, subject, outputdir)
        cls.create_outputdirs(parameter_template, subject, outputdir)
        source_filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"
        shutil.copy(source_filename, target_filename)
        return target_filename
