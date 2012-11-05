from morphologist.analysis import StepFlow, InputParameters, OutputParameters
from morphologist.steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain


class IntraAnalysisStepFlow(StepFlow):

    def __init__(self):
        self._bias_correction = BiasCorrection()
        self._histogram_analysis = HistogramAnalysis()
        self._brain_segmentation = BrainSegmentation()
        self._split_brain = SplitBrain()  
        self._steps = [self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 

        # TODO
        self.input_params = InputParameters(file_param_names=['mri',
                                                              'commissure_coordinates'], 
                                            other_param_names=['erosion_size',
                                                               'bary_factor'])

        # TODO
        self.output_params = OutputParameters(file_param_names=['hfiltered',
                                                                'white_ridges',
                                                                'edges',
                                                                'variance',
                                                                'mri_corrected',
                                                                'histo_analysis',
                                                                'brain_mask',
                                                                'split_mask'])


    def propagate_parameters(self):
        
        self._bias_correction.mri = self.input_params.mri
        self._bias_correction.commissure_coordinates = self.input_params.commissure_coordinates

        self._bias_correction.hfiltered = self.output_params.hfiltered
        self._bias_correction.white_ridges = self.output_params.white_ridges
        self._bias_correction.edges = self.output_params.edges
        self._bias_correction.variance = self.output_params.variance
        self._bias_correction.mri_corrected = self.output_params.mri_corrected


        self._histogram_analysis.mri_corrected = self._bias_correction.mri_corrected
        self._histogram_analysis.hfiltered = self._bias_correction.hfiltered
        self._histogram_analysis.white_ridges = self._bias_correction.white_ridges
        
        self._histogram_analysis.histo_analysis = self.output_params.histo_analysis


        self._brain_segmentation.mri_corrected = self._bias_correction.mri_corrected
        self._brain_segmentation.commissure_coordinates = self.input_params.commissure_coordinates
        self._brain_segmentation.white_ridges = self._bias_correction.white_ridges
        self._brain_segmentation.edges = self._bias_correction.edges
        self._brain_segmentation.variance = self._bias_correction.variance
        self._brain_segmentation.histo_analysis = self._histogram_analysis.histo_analysis        
        self._brain_segmentation.erosion_size = self.input_params.erosion_size

        self._brain_segmentation.brain_mask = self.output_params.brain_mask

  
        self._split_brain.mri_corrected = self._bias_correction.mri_corrected
        self._split_brain.brain_mask = self._brain_segmentation.brain_mask
        self._split_brain.white_ridges = self._bias_correction.white_ridges
        self._split_brain.histo_analysis = self._histogram_analysis.histo_analysis
        self._split_brain.commissure_coordiantes = self.input_params.commissure_coordinates
        self._split_brain.bary_factor = self.input_params.bary_factor

        self._split_brain.split_mask = self.output_params.split_mask


