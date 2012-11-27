from morphologist.intra_analysis import IntraAnalysis, IntraAnalysisStepFlow
from morphologist.intra_analysis import BrainvisaIntraAnalysisParameterTemplate
from morphologist.tests.mocks.intra_analysis_steps import MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain


class MockIntraAnalysis(IntraAnalysis):
    
    def create_step_flow(self):
        return MockIntraAnalysisStepFlow()


class MockIntraAnalysisStepFlow(IntraAnalysisStepFlow):

    def init_steps(self):

        mock_out_files = BrainvisaIntraAnalysisParameterTemplate.get_output_params("hyperion",
                        "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/test")
        self._bias_correction = MockBiasCorrection(mock_out_files)
        self._histogram_analysis = MockHistogramAnalysis(mock_out_files)
        self._brain_segmentation = MockBrainSegmentation(mock_out_files)
        self._split_brain = MockSplitBrain(mock_out_files)  
        self._steps = [self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 

        


