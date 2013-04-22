import os
import glob
import re
import shutil

from morphologist.core.subject import Subject
from morphologist.core.analysis import Analysis, Parameters, \
                                  ImportationError, ParameterTemplate
from morphologist.core.utils import create_directory_if_missing, create_directories_if_missing
from morphologist.intra_analysis.steps import ImageImportation, \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    GreyWhite, SpatialNormalization, Grey, GreySurface, WhiteSurface, Sulci, SulciLabelling, Morphometry
from morphologist.intra_analysis import constants
from morphologist.intra_analysis.parameters import BrainvisaIntraAnalysisParameterTemplate, \
                                                    DefaultIntraAnalysisParameterTemplate, \
                                                    IntraAnalysisParameterTemplate, \
                                                    IntraAnalysisParameterNames


class IntraAnalysis(Analysis):
    PARAMETER_TEMPLATES = [BrainvisaIntraAnalysisParameterTemplate, 
                           DefaultIntraAnalysisParameterTemplate]
    
    def __init__(self, parameter_template):
        super(IntraAnalysis, self).__init__(parameter_template) 
        self.inputs = IntraAnalysisParameterTemplate.get_empty_inputs()
        self.outputs = IntraAnalysisParameterTemplate.get_empty_outputs()

    def _init_steps(self):
        self._normalization = SpatialNormalization()
        self._bias_correction = BiasCorrection()
        self._histogram_analysis = HistogramAnalysis()
        self._brain_segmentation = BrainSegmentation()
        self._split_brain = SplitBrain()
        self._left_grey_white = GreyWhite(constants.LEFT)
        self._right_grey_white = GreyWhite(constants.RIGHT)
        self._left_grey = Grey()
        self._right_grey = Grey()
        self._left_grey_surface = GreySurface(constants.LEFT)
        self._right_grey_surface = GreySurface(constants.RIGHT)
        self._left_white_surface = WhiteSurface()
        self._right_white_surface = WhiteSurface()
        self._left_sulci = Sulci(constants.LEFT)
        self._right_sulci = Sulci(constants.RIGHT)
        self._left_sulci_labelling = SulciLabelling(constants.LEFT)
        self._right_sulci_labelling = SulciLabelling(constants.RIGHT)
        self._left_native_morphometry = Morphometry(constants.LEFT,
                                                    normalized=False)
        self._right_native_morphometry = Morphometry(constants.RIGHT,
                                                     normalized=False)
        self._left_normalized_morphometry = Morphometry(constants.LEFT,
                                                        normalized=True)
        self._right_normalized_morphometry = Morphometry(constants.RIGHT,
                                                         normalized=True)
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
                       self._right_sulci_labelling,
                       self._left_native_morphometry,
                       self._right_native_morphometry,
                       self._left_normalized_morphometry,
                       self._right_normalized_morphometry,
                    ]

    @classmethod
    def get_default_parameter_template_name(cls):
        return BrainvisaIntraAnalysisParameterTemplate.name
        
    def import_data(self, subject):
        import_step = ImageImportation()
        import_step.inputs.input = subject.filename
        import_step.outputs.output = self.parameter_template.get_subject_filename(subject)
        self.parameter_template.create_outputdirs(subject)
        if import_step.run() != 0:
            raise ImportationError("The importation failed for the subject %s."
                                   % str(subject))
        return import_step.outputs.output

    def propagate_parameters(self):
        self._normalization.inputs.mri = self.inputs[IntraAnalysisParameterNames.MRI]
        self._normalization.outputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._normalization.outputs.talairach_transformation = self.outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        
        self._bias_correction.inputs.mri = self.inputs[IntraAnalysisParameterNames.MRI]
        self._bias_correction.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._bias_correction.outputs.hfiltered = self.outputs[IntraAnalysisParameterNames.HFILTERED]
        self._bias_correction.outputs.white_ridges = self.outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        self._bias_correction.outputs.edges = self.outputs[IntraAnalysisParameterNames.EDGES]
        self._bias_correction.outputs.variance = self.outputs[IntraAnalysisParameterNames.VARIANCE]
        self._bias_correction.outputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]

        self._histogram_analysis.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI] 
        self._histogram_analysis.inputs.hfiltered = self.outputs[IntraAnalysisParameterNames.HFILTERED] 
        self._histogram_analysis.inputs.white_ridges = self.outputs[IntraAnalysisParameterNames.WHITE_RIDGES] 
        self._histogram_analysis.outputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._histogram_analysis.outputs.histogram = self.outputs[IntraAnalysisParameterNames.HISTOGRAM]

        self._brain_segmentation.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._brain_segmentation.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._brain_segmentation.inputs.edges = self.outputs[IntraAnalysisParameterNames.EDGES]
        self._brain_segmentation.inputs.variance = self.outputs[IntraAnalysisParameterNames.VARIANCE]
        self._brain_segmentation.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._brain_segmentation.inputs.erosion_size = self.inputs[IntraAnalysisParameterNames.EROSION_SIZE]
        self._brain_segmentation.inputs.white_ridges = self.outputs[IntraAnalysisParameterNames.WHITE_RIDGES]
        self._brain_segmentation.outputs.brain_mask = self.outputs[IntraAnalysisParameterNames.BRAIN_MASK]
        self._brain_segmentation.outputs.white_ridges = self.outputs[IntraAnalysisParameterNames.REFINED_WHITE_RIDGES]

        self._split_brain.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._split_brain.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._split_brain.inputs.brain_mask = self.outputs[IntraAnalysisParameterNames.BRAIN_MASK] 
        self._split_brain.inputs.white_ridges = self.outputs[IntraAnalysisParameterNames.REFINED_WHITE_RIDGES]
        self._split_brain.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._split_brain.inputs.bary_factor = self.inputs[IntraAnalysisParameterNames.BARY_FACTOR]
        self._split_brain.outputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]

        self._left_grey_white.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._left_grey_white.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._left_grey_white.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._left_grey_white.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._left_grey_white.inputs.edges = self.outputs[IntraAnalysisParameterNames.EDGES]
        self._left_grey_white.outputs.grey_white = self.outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]

        self._right_grey_white.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._right_grey_white.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._right_grey_white.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._right_grey_white.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._right_grey_white.inputs.edges = self.outputs[IntraAnalysisParameterNames.EDGES]
        self._right_grey_white.outputs.grey_white = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]

        self._left_grey.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._left_grey.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._left_grey.inputs.grey_white = self.outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        self._left_grey.outputs.grey = self.outputs[IntraAnalysisParameterNames.LEFT_GREY]

        self._right_grey.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._right_grey.inputs.histo_analysis = self.outputs[IntraAnalysisParameterNames.HISTO_ANALYSIS]
        self._right_grey.inputs.grey_white = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
        self._right_grey.outputs.grey = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY]

        self._left_grey_surface.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI] 
        self._left_grey_surface.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._left_grey_surface.inputs.grey = self.outputs[IntraAnalysisParameterNames.LEFT_GREY]
        self._left_grey_surface.outputs.grey_surface = self.outputs[IntraAnalysisParameterNames.LEFT_GREY_SURFACE]

        self._right_grey_surface.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._right_grey_surface.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._right_grey_surface.inputs.grey = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        self._right_grey_surface.outputs.grey_surface = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE]

        self._left_white_surface.inputs.grey = self.outputs[IntraAnalysisParameterNames.LEFT_GREY]
        self._left_white_surface.outputs.white_surface = self.outputs[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]

        self._right_white_surface.inputs.grey = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        self._right_white_surface.outputs.white_surface = self.outputs[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]

        self._left_sulci.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._left_sulci.inputs.grey = self.outputs[IntraAnalysisParameterNames.LEFT_GREY]
        self._left_sulci.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._left_sulci.inputs.talairach_transformation = self.outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        self._left_sulci.inputs.grey_white = self.outputs[IntraAnalysisParameterNames.LEFT_GREY_WHITE]
        self._left_sulci.inputs.white_surface = self.outputs[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE]
        self._left_sulci.inputs.grey_surface = self.outputs[IntraAnalysisParameterNames.LEFT_GREY_SURFACE]
        self._left_sulci.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._left_sulci.outputs.sulci = self.outputs[IntraAnalysisParameterNames.LEFT_SULCI]
        self._left_sulci.outputs.sulci_data = self.outputs[IntraAnalysisParameterNames.LEFT_SULCI_DATA]
 
        self._right_sulci.inputs.corrected_mri = self.outputs[IntraAnalysisParameterNames.CORRECTED_MRI]
        self._right_sulci.inputs.grey = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY]
        self._right_sulci.inputs.split_mask = self.outputs[IntraAnalysisParameterNames.SPLIT_MASK]
        self._right_sulci.inputs.talairach_transformation = self.outputs[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION]
        self._right_sulci.inputs.grey_white = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY_WHITE]
        self._right_sulci.inputs.white_surface = self.outputs[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE]
        self._right_sulci.inputs.grey_surface = self.outputs[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE]
        self._right_sulci.inputs.commissure_coordinates = self.outputs[IntraAnalysisParameterNames.COMMISSURE_COORDINATES]
        self._right_sulci.outputs.sulci = self.outputs[IntraAnalysisParameterNames.RIGHT_SULCI]
        self._right_sulci.outputs.sulci_data = self.outputs[IntraAnalysisParameterNames.RIGHT_SULCI_DATA]

        self._left_sulci_labelling.inputs.sulci = self.outputs[IntraAnalysisParameterNames.LEFT_SULCI]
        self._left_sulci_labelling.outputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.LEFT_LABELED_SULCI]
        self._left_sulci_labelling.outputs.labeled_sulci_data = self.outputs[IntraAnalysisParameterNames.LEFT_LABELED_SULCI_DATA]

        self._right_sulci_labelling.inputs.sulci = self.outputs[IntraAnalysisParameterNames.RIGHT_SULCI]
        self._right_sulci_labelling.outputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI]
        self._right_sulci_labelling.outputs.labeled_sulci_data = self.outputs[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI_DATA]

        self._left_native_morphometry.inputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.LEFT_LABELED_SULCI]
        self._left_native_morphometry.outputs.morphometry = self.outputs[IntraAnalysisParameterNames.LEFT_NATIVE_MORPHOMETRY_CSV]

        self._right_native_morphometry.inputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI]
        self._right_native_morphometry.outputs.morphometry = self.outputs[IntraAnalysisParameterNames.RIGHT_NATIVE_MORPHOMETRY_CSV]

        self._left_normalized_morphometry.inputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.LEFT_LABELED_SULCI]
        self._left_normalized_morphometry.outputs.morphometry = self.outputs[IntraAnalysisParameterNames.LEFT_NORMALIZED_MORPHOMETRY_CSV]

        self._right_normalized_morphometry.inputs.labeled_sulci = self.outputs[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI]
        self._right_normalized_morphometry.outputs.morphometry = self.outputs[IntraAnalysisParameterNames.RIGHT_NORMALIZED_MORPHOMETRY_CSV]
