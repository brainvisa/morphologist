import shutil

from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis import BrainvisaIntraAnalysisParameterTemplate
from morphologist.tests.intra_analysis.mocks.steps import MockSpatialNormalization, \
    MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain, \
    MockLeftGreyWhite, MockRightGreyWhite, MockGrey, MockWhiteSurface


class MockIntraAnalysis(IntraAnalysis):

    def __init__(self):
        super(MockIntraAnalysis, self).__init__()
        self._init_steps()   


    def _init_steps(self):
        mock_out_files = BrainvisaIntraAnalysisParameterTemplate.get_output_params("test", "hyperion",
                        "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database")
        self._normalization = MockSpatialNormalization(mock_out_files)
        self._bias_correction = MockBiasCorrection(mock_out_files)
        self._histogram_analysis = MockHistogramAnalysis(mock_out_files)
        self._brain_segmentation = MockBrainSegmentation(mock_out_files)
        self._split_brain = MockSplitBrain(mock_out_files)  
        self._left_grey_white = MockLeftGreyWhite(mock_out_files)  
        self._right_grey_white = MockRightGreyWhite(mock_out_files)
        self._left_grey = MockGrey(mock_out_files[IntraAnalysis.LEFT_GREY])
        self._right_grey = MockGrey(mock_out_files[IntraAnalysis.RIGHT_GREY])
        self._left_white_surface = MockWhiteSurface(mock_out_files[IntraAnalysis.LEFT_WHITE_SURFACE])
        self._right_white_surface = MockWhiteSurface(mock_out_files[IntraAnalysis.RIGHT_WHITE_SURFACE])
        self._steps = [self._normalization, 
                       self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain,
                       self._left_grey_white,
                       self._right_grey_white, 
                       self._left_grey, 
                       self._right_grey,
                       self._left_white_surface, 
                       self._right_white_surface]

    @classmethod
    def import_data(cls, parameter_template, filename, groupname, subjectname, outputdir):
        target_filename = cls.get_mri_path(parameter_template, 
                                           groupname,
                                           subjectname,
                                           outputdir)
        cls.create_outputdirs(parameter_template, groupname, subjectname, outputdir)
        source_filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"
        shutil.copy(source_filename, target_filename)
        return target_filename
