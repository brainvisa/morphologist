import os

from morphologist.analysis import Analysis, InputParameters, OutputParameters, \
                                  ImportationError, ParameterTemplate
from morphologist.intra_analysis_steps import ImageImportation, \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    GreyWhite, SpatialNormalization, Grey, GreySurface, WhiteSurface, Sulci, SulciLabelling
import morphologist.intra_analysis_constants as constants


class IntraAnalysis(Analysis):
    # TODO: change string by a number
    BRAINVISA_PARAM_TEMPLATE = 'brainvisa'
    DEFAULT_PARAM_TEMPLATE = 'default'
    PARAMETER_TEMPLATES = [BRAINVISA_PARAM_TEMPLATE, DEFAULT_PARAM_TEMPLATE]
    param_template_map = {}

    # intra analysis parameters (inputs / outputs)
    MRI = 'mri'
    COMMISSURE_COORDINATES = 'commissure_coordinates'
    TALAIRACH_TRANSFORMATION = 'talairach_transformation'
    EROSION_SIZE = 'erosion_size' 
    BARY_FACTOR = 'bary_factor'
    HFILTERED = 'hfiltered'
    WHITE_RIDGES = 'white_ridges'
    REFINED_WHITE_RIDGES = 'refined_white_ridges'
    EDGES = 'edges'
    VARIANCE = 'variance'
    CORRECTED_MRI = 'corrected_mri'
    HISTO_ANALYSIS = 'histo_analysis'
    HISTOGRAM = 'histogram'
    BRAIN_MASK = 'brain_mask'
    SPLIT_MASK = 'split_mask'
    LEFT_GREY_WHITE = 'left_grey_white'
    RIGHT_GREY_WHITE = 'right_grey_white'
    LEFT_GREY = 'left_grey'
    RIGHT_GREY = 'right_grey'
    LEFT_GREY_SURFACE = 'left_grey_surface'
    RIGHT_GREY_SURFACE = 'right_grey_surface'
    LEFT_WHITE_SURFACE = 'left_white_surface'
    RIGHT_WHITE_SURFACE = 'right_white_surface'
    LEFT_SULCI = 'left_sulci'
    RIGHT_SULCI = 'right_sulci'
    LEFT_LABELED_SULCI = 'left_labeled_sulci'
    RIGHT_LABELED_SULCI = 'right_labeled_sulci'
    # XXX _DATA are used to hardcode .data directory generated with .arg files
    LEFT_SULCI_DATA = 'left_sulci_data'
    RIGHT_SULCI_DATA = 'right_sulci_data'
    LEFT_LABELED_SULCI_DATA = 'left_labeled_sulci_data'
    RIGHT_LABELED_SULCI_DATA = 'right_labeled_sulci_data'

    # TODO: reimplement a standard python method ?
    @classmethod
    def _init_class(cls):
        cls.param_template_map[cls.BRAINVISA_PARAM_TEMPLATE] = \
                        BrainvisaIntraAnalysisParameterTemplate
        cls.param_template_map[cls.DEFAULT_PARAM_TEMPLATE] = \
                        DefaultIntraAnalysisParameterTemplate
  
    def __init__(self):
        super(IntraAnalysis, self).__init__() 
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

        import_step = ImageImportation()
        import_step.inputs.input = subject.filename
        import_step.outputs.output = cls.get_mri_path(parameter_template, subject, outputdir)
        cls.create_outputdirs(parameter_template, subject, outputdir)
        if import_step.run() != 0:
            raise ImportationError("The importation failed for the subject %s."
                                   % subject.id())
        return import_step.outputs.output

    def propagate_parameters(self):
        self._normalization.inputs.mri = self.inputs[IntraAnalysis.MRI]
        self._normalization.outputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._normalization.outputs.talairach_transformation = self.outputs[IntraAnalysis.TALAIRACH_TRANSFORMATION]
        
        self._bias_correction.inputs.mri = self.inputs[IntraAnalysis.MRI]
        self._bias_correction.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._bias_correction.outputs.hfiltered = self.outputs[IntraAnalysis.HFILTERED]
        self._bias_correction.outputs.white_ridges = self.outputs[IntraAnalysis.WHITE_RIDGES]
        self._bias_correction.outputs.edges = self.outputs[IntraAnalysis.EDGES]
        self._bias_correction.outputs.variance = self.outputs[IntraAnalysis.VARIANCE]
        self._bias_correction.outputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]

        self._histogram_analysis.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI] 
        self._histogram_analysis.inputs.hfiltered = self.outputs[IntraAnalysis.HFILTERED] 
        self._histogram_analysis.inputs.white_ridges = self.outputs[IntraAnalysis.WHITE_RIDGES] 
        self._histogram_analysis.outputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._histogram_analysis.outputs.histogram = self.outputs[IntraAnalysis.HISTOGRAM]

        self._brain_segmentation.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._brain_segmentation.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._brain_segmentation.inputs.edges = self.outputs[IntraAnalysis.EDGES]
        self._brain_segmentation.inputs.variance = self.outputs[IntraAnalysis.VARIANCE]
        self._brain_segmentation.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._brain_segmentation.inputs.erosion_size = self.inputs[IntraAnalysis.EROSION_SIZE]
        self._brain_segmentation.inputs.white_ridges = self.outputs[IntraAnalysis.WHITE_RIDGES]
        self._brain_segmentation.outputs.brain_mask = self.outputs[IntraAnalysis.BRAIN_MASK]
        self._brain_segmentation.outputs.white_ridges = self.outputs[IntraAnalysis.REFINED_WHITE_RIDGES]

        self._split_brain.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._split_brain.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._split_brain.inputs.brain_mask = self.outputs[IntraAnalysis.BRAIN_MASK] 
        self._split_brain.inputs.white_ridges = self.outputs[IntraAnalysis.REFINED_WHITE_RIDGES]
        self._split_brain.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._split_brain.inputs.bary_factor = self.inputs[IntraAnalysis.BARY_FACTOR]
        self._split_brain.outputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]

        self._left_grey_white.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._left_grey_white.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._left_grey_white.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._left_grey_white.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._left_grey_white.inputs.edges = self.outputs[IntraAnalysis.EDGES]
        self._left_grey_white.outputs.grey_white = self.outputs[IntraAnalysis.LEFT_GREY_WHITE]

        self._right_grey_white.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._right_grey_white.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._right_grey_white.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._right_grey_white.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._right_grey_white.inputs.edges = self.outputs[IntraAnalysis.EDGES]
        self._right_grey_white.outputs.grey_white = self.outputs[IntraAnalysis.RIGHT_GREY_WHITE]

        self._left_grey.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._left_grey.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._left_grey.inputs.grey_white = self.outputs[IntraAnalysis.LEFT_GREY_WHITE]
        self._left_grey.outputs.grey = self.outputs[IntraAnalysis.LEFT_GREY]

        self._right_grey.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._right_grey.inputs.histo_analysis = self.outputs[IntraAnalysis.HISTO_ANALYSIS]
        self._right_grey.inputs.grey_white = self.outputs[IntraAnalysis.RIGHT_GREY_WHITE]
        self._right_grey.outputs.grey = self.outputs[IntraAnalysis.RIGHT_GREY]

        self._left_grey_surface.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI] 
        self._left_grey_surface.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._left_grey_surface.inputs.grey = self.outputs[IntraAnalysis.LEFT_GREY]
        self._left_grey_surface.outputs.grey_surface = self.outputs[IntraAnalysis.LEFT_GREY_SURFACE]

        self._right_grey_surface.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._right_grey_surface.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._right_grey_surface.inputs.grey = self.outputs[IntraAnalysis.RIGHT_GREY]
        self._right_grey_surface.outputs.grey_surface = self.outputs[IntraAnalysis.RIGHT_GREY_SURFACE]

        self._left_white_surface.inputs.grey = self.outputs[IntraAnalysis.LEFT_GREY]
        self._left_white_surface.outputs.white_surface = self.outputs[IntraAnalysis.LEFT_WHITE_SURFACE]

        self._right_white_surface.inputs.grey = self.outputs[IntraAnalysis.RIGHT_GREY]
        self._right_white_surface.outputs.white_surface = self.outputs[IntraAnalysis.RIGHT_WHITE_SURFACE]

        self._left_sulci.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._left_sulci.inputs.grey = self.outputs[IntraAnalysis.LEFT_GREY]
        self._left_sulci.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._left_sulci.inputs.talairach_transformation = self.outputs[IntraAnalysis.TALAIRACH_TRANSFORMATION]
        self._left_sulci.inputs.grey_white = self.outputs[IntraAnalysis.LEFT_GREY_WHITE]
        self._left_sulci.inputs.white_surface = self.outputs[IntraAnalysis.LEFT_WHITE_SURFACE]
        self._left_sulci.inputs.grey_surface = self.outputs[IntraAnalysis.LEFT_GREY_SURFACE]
        self._left_sulci.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._left_sulci.outputs.sulci = self.outputs[IntraAnalysis.LEFT_SULCI]
        self._left_sulci.outputs.sulci_data = self.outputs[IntraAnalysis.LEFT_SULCI_DATA]
 
        self._right_sulci.inputs.corrected_mri = self.outputs[IntraAnalysis.CORRECTED_MRI]
        self._right_sulci.inputs.grey = self.outputs[IntraAnalysis.RIGHT_GREY]
        self._right_sulci.inputs.split_mask = self.outputs[IntraAnalysis.SPLIT_MASK]
        self._right_sulci.inputs.talairach_transformation = self.outputs[IntraAnalysis.TALAIRACH_TRANSFORMATION]
        self._right_sulci.inputs.grey_white = self.outputs[IntraAnalysis.RIGHT_GREY_WHITE]
        self._right_sulci.inputs.white_surface = self.outputs[IntraAnalysis.RIGHT_WHITE_SURFACE]
        self._right_sulci.inputs.grey_surface = self.outputs[IntraAnalysis.RIGHT_GREY_SURFACE]
        self._right_sulci.inputs.commissure_coordinates = self.outputs[IntraAnalysis.COMMISSURE_COORDINATES]
        self._right_sulci.outputs.sulci = self.outputs[IntraAnalysis.RIGHT_SULCI]
        self._right_sulci.outputs.sulci_data = self.outputs[IntraAnalysis.RIGHT_SULCI_DATA]

        self._left_sulci_labelling.inputs.sulci = self.outputs[IntraAnalysis.LEFT_SULCI]
        self._left_sulci_labelling.outputs.labeled_sulci = self.outputs[IntraAnalysis.LEFT_LABELED_SULCI]
        self._left_sulci_labelling.outputs.labeled_sulci_data = self.outputs[IntraAnalysis.LEFT_LABELED_SULCI_DATA]

        self._right_sulci_labelling.inputs.sulci = self.outputs[IntraAnalysis.RIGHT_SULCI]
        self._right_sulci_labelling.outputs.labeled_sulci = self.outputs[IntraAnalysis.RIGHT_LABELED_SULCI]
        self._right_sulci_labelling.outputs.labeled_sulci_data = self.outputs[IntraAnalysis.RIGHT_LABELED_SULCI_DATA]


    @classmethod
    def get_mri_path(cls, parameter_template, subject, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        return param_template_instance.get_mri_path(subject, directory)
    
    @classmethod
    def create_outputdirs(cls, parameter_template, subject, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        param_template_instance.create_outputdirs(subject, directory)


class IntraAnalysisParameterTemplate(ParameterTemplate):
    input_file_param_names = [IntraAnalysis.MRI]
    input_other_param_names = [IntraAnalysis.EROSION_SIZE, IntraAnalysis.BARY_FACTOR]
    output_file_param_names = [IntraAnalysis.COMMISSURE_COORDINATES,
                               IntraAnalysis.TALAIRACH_TRANSFORMATION,
                               IntraAnalysis.HFILTERED,
                               IntraAnalysis.WHITE_RIDGES,
                               IntraAnalysis.REFINED_WHITE_RIDGES,
                               IntraAnalysis.EDGES,
                               IntraAnalysis.VARIANCE,
                               IntraAnalysis.CORRECTED_MRI,
                               IntraAnalysis.HISTO_ANALYSIS,
                               IntraAnalysis.HISTOGRAM,
                               IntraAnalysis.BRAIN_MASK,
                               IntraAnalysis.SPLIT_MASK,
                               IntraAnalysis.LEFT_GREY_WHITE,
                               IntraAnalysis.RIGHT_GREY_WHITE,
                               IntraAnalysis.LEFT_GREY,
                               IntraAnalysis.RIGHT_GREY,
                               IntraAnalysis.LEFT_GREY_SURFACE,
                               IntraAnalysis.RIGHT_GREY_SURFACE,
                               IntraAnalysis.LEFT_WHITE_SURFACE,
                               IntraAnalysis.RIGHT_WHITE_SURFACE,
                               IntraAnalysis.LEFT_SULCI,
                               IntraAnalysis.RIGHT_SULCI,
                               IntraAnalysis.LEFT_SULCI_DATA,
                               IntraAnalysis.RIGHT_SULCI_DATA,
                               IntraAnalysis.LEFT_LABELED_SULCI,
                               IntraAnalysis.RIGHT_LABELED_SULCI,
                               IntraAnalysis.LEFT_LABELED_SULCI_DATA,
                               IntraAnalysis.RIGHT_LABELED_SULCI_DATA]

    @classmethod
    def get_empty_inputs(cls):
        return InputParameters(cls.input_file_param_names,
                               cls.input_other_param_names)

    @classmethod
    def get_empty_outputs(cls):
        return OutputParameters(cls.output_file_param_names)
    
    @classmethod
    def get_mri_path(cls, subject, directory):
        raise Exception("IntraAnalysisParameterTemplate is an Abstract class.")
    
    @classmethod
    def get_inputs(cls, subject):
        # input_filename should be in cls.get_mri_path()
        # TODO raise an exception if it not the case ?
        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)
        parameters[IntraAnalysis.MRI] = subject.filename
        parameters[IntraAnalysis.EROSION_SIZE] = 1.8
        parameters[IntraAnalysis.BARY_FACTOR] = 0.6
        return parameters


class BrainvisaIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):
    ACQUISITION = "default_acquisition"
    ANALYSIS = "default_analysis"
    REGISTRATION = "registration"
    MODALITY = "t1mri"
    SEGMENTATION = "segmentation"
    SURFACE = "mesh"
    FOLDS = "folds"
    FOLDS_3_1 = "3.1"
    SESSION_AUTO = "default_session_auto"
    
    @classmethod
    def get_mri_path(cls, subject, directory):
        return os.path.join(directory, subject.groupname, subject.subjectname, 
                            cls.MODALITY, cls.ACQUISITION, subject.subjectname + ".nii")

    @classmethod
    def get_outputs(cls, subject, outputdir):
        subjectname = subject.subjectname
        default_acquisition_path = os.path.join(outputdir, subject.groupname, subjectname, 
                                                cls.MODALITY, cls.ACQUISITION)
        registration_path = os.path.join(default_acquisition_path, cls.REGISTRATION)
        default_analysis_path = os.path.join(default_acquisition_path, cls.ANALYSIS) 
          
        segmentation_path = os.path.join(default_analysis_path, cls.SEGMENTATION)
        surface_path = os.path.join(segmentation_path, cls.SURFACE)

        folds_path = os.path.join(default_analysis_path, cls.FOLDS, cls.FOLDS_3_1)
  
        session_auto_path = os.path.join(folds_path, cls.SESSION_AUTO)
 
        parameters = OutputParameters(cls.output_file_param_names)
        parameters[IntraAnalysis.COMMISSURE_COORDINATES] = os.path.join(default_acquisition_path, 
                                                   "%s.APC" % subjectname)
        parameters[IntraAnalysis.TALAIRACH_TRANSFORMATION] = os.path.join(registration_path, 
                                                         "RawT1-%s_%s_TO_Talairach-ACPC.trm" 
                                                         % (subjectname, cls.ACQUISITION))
        parameters[IntraAnalysis.HFILTERED] = os.path.join(default_analysis_path, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters[IntraAnalysis.WHITE_RIDGES] = os.path.join(default_analysis_path, 
                                            "raw_whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.REFINED_WHITE_RIDGES] = os.path.join(default_analysis_path, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.EDGES] = os.path.join(default_analysis_path, 
                                            "edges_%s.nii" % subjectname)
        parameters[IntraAnalysis.CORRECTED_MRI] = os.path.join(default_analysis_path, 
                                            "nobias_%s.nii" % subjectname)
        parameters[IntraAnalysis.VARIANCE] = os.path.join(default_analysis_path, 
                                            "variance_%s.nii" % subjectname)
        parameters[IntraAnalysis.HISTO_ANALYSIS] = os.path.join(default_analysis_path, 
                                            "nobias_%s.han" % subjectname)
        parameters[IntraAnalysis.HISTOGRAM] = os.path.join(default_analysis_path, 
                                            "nobias_%s.his" % subjectname)
        parameters[IntraAnalysis.BRAIN_MASK] = os.path.join(segmentation_path, 
                                            "brain_%s.nii" % subjectname)
        parameters[IntraAnalysis.SPLIT_MASK] = os.path.join(segmentation_path, 
                                            "voronoi_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY_WHITE] = os.path.join(\
                        segmentation_path, "Lgrey_white_%s.nii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY_WHITE] = os.path.join(\
                        segmentation_path, "Rgrey_white_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY] = os.path.join(\
                        segmentation_path, "Lcortex_%s.nii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY] = os.path.join(\
                        segmentation_path, "Rcortex_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY_SURFACE] = os.path.join(\
                        surface_path, "%s_Lhemi.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY_SURFACE] = os.path.join(\
                        surface_path, "%s_Rhemi.gii" % subjectname)
        parameters[IntraAnalysis.LEFT_WHITE_SURFACE] = os.path.join(\
                        surface_path, "%s_Lwhite.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_WHITE_SURFACE] = os.path.join(\
                        surface_path, "%s_Rwhite.gii" % subjectname)
        parameters[IntraAnalysis.LEFT_SULCI] = os.path.join(\
                        folds_path, "L%s.arg" % subjectname)
        parameters[IntraAnalysis.RIGHT_SULCI] = os.path.join(\
                        folds_path, "R%s.arg" % subjectname)
        parameters[IntraAnalysis.LEFT_SULCI_DATA] = os.path.join(\
                        folds_path, "L%s.data" % subjectname)
        parameters[IntraAnalysis.RIGHT_SULCI_DATA] = os.path.join(\
                        folds_path, "R%s.data" % subjectname)
        parameters[IntraAnalysis.LEFT_LABELED_SULCI] = os.path.join(\
                        session_auto_path, "L%s_default_session_auto.arg" % subjectname)
        parameters[IntraAnalysis.RIGHT_LABELED_SULCI] = os.path.join(\
                        session_auto_path, "R%s_default_session_auto.arg" % subjectname)
        parameters[IntraAnalysis.LEFT_LABELED_SULCI_DATA] = os.path.join(\
                        session_auto_path, "L%s_default_session_auto.data" % subjectname)
        parameters[IntraAnalysis.RIGHT_LABELED_SULCI_DATA] = os.path.join(\
                        session_auto_path, "R%s_default_session_auto.data" % subjectname)


        return parameters

    @classmethod
    def create_outputdirs(cls, subject, outputdir):
        group_path = os.path.join(outputdir, subject.groupname)
        create_directory_if_missing(group_path)
        
        subject_path = os.path.join(group_path, subject.subjectname)
        create_directory_if_missing(subject_path)
        
        t1mri_path = os.path.join(subject_path, cls.MODALITY)
        create_directory_if_missing(t1mri_path)
        
        default_acquisition_path = os.path.join(t1mri_path, cls.ACQUISITION)
        create_directory_if_missing(default_acquisition_path)
        
        registration_path = os.path.join(default_acquisition_path, cls.REGISTRATION)
        create_directory_if_missing(registration_path)
        
        default_analysis_path = os.path.join(default_acquisition_path, cls.ANALYSIS) 
        create_directory_if_missing(default_analysis_path)
        
        segmentation_path = os.path.join(default_analysis_path, cls.SEGMENTATION)
        create_directory_if_missing(segmentation_path)
        
        surface_path = os.path.join(segmentation_path, cls.SURFACE)
        create_directory_if_missing(surface_path)

        folds_path = os.path.join(default_analysis_path, cls.FOLDS)
        create_directory_if_missing(folds_path)
  
        folds_3_1_path = os.path.join(default_analysis_path, cls.FOLDS, cls.FOLDS_3_1)
        create_directory_if_missing(folds_3_1_path)
 
        session_auto_path = os.path.join(folds_3_1_path, cls.SESSION_AUTO)
        create_directory_if_missing(session_auto_path)

           
class DefaultIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):

    @classmethod
    def get_mri_path(cls, subject, directory):
        return os.path.join(directory, subject.groupname, subject.subjectname, 
                            subject.subjectname + ".nii")

    @classmethod
    def get_outputs(cls, subject, outputdir):
        parameters = OutputParameters(cls.output_file_param_names)

        subjectname = subject.subjectname
        subject_path = os.path.join(outputdir, subject.groupname, subjectname)
        parameters[IntraAnalysis.COMMISSURE_COORDINATES] = os.path.join(subject_path, 
                                                         "%s.APC" %subjectname)
        parameters[IntraAnalysis.TALAIRACH_TRANSFORMATION] = os.path.join(subject_path,
                                                            "RawT1-%s_TO_Talairach-ACPC.trm" 
                                                            % subjectname)
        parameters[IntraAnalysis.HFILTERED] = os.path.join(subject_path, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters[IntraAnalysis.WHITE_RIDGES] = os.path.join(subject_path, 
                                            "raw_whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.REFINED_WHITE_RIDGES] = os.path.join(subject_path, 
                                            "refined_whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.EDGES] = os.path.join(subject_path, 
                                            "edges_%s.nii" % subjectname)
        parameters[IntraAnalysis.CORRECTED_MRI] = os.path.join(subject_path, 
                                            "nobias_%s.nii" % subjectname)
        parameters[IntraAnalysis.VARIANCE] = os.path.join(subject_path, 
                                            "variance_%s.nii" % subjectname)
        parameters[IntraAnalysis.HISTO_ANALYSIS] = os.path.join(subject_path, 
                                            "nobias_%s.han" % subjectname)
        parameters[IntraAnalysis.HISTOGRAM] = os.path.join(subject_path, 
                                            "nobias_%s.his" % subjectname)
        parameters[IntraAnalysis.BRAIN_MASK] = os.path.join(subject_path, 
                                            "brain_%s.nii" % subjectname)
        parameters[IntraAnalysis.SPLIT_MASK] = os.path.join(subject_path, 
                                            "voronoi_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY_WHITE] = os.path.join(\
                subject_path, "left_grey_white_%s.nii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY_WHITE] = os.path.join(\
                subject_path, "right_grey_white_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY] = os.path.join(\
                subject_path, "left_grey_%s.nii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY] = os.path.join(\
                subject_path, "right_grey_%s.nii" % subjectname)
        parameters[IntraAnalysis.LEFT_GREY_SURFACE] = os.path.join(\
                        subject_path, "left_grey_surface_%s.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_GREY_SURFACE] = os.path.join(\
                        subject_path, "right_grey_surface_%s.gii" % subjectname)
        parameters[IntraAnalysis.LEFT_WHITE_SURFACE] = os.path.join(\
                subject_path, "left_white_surface_%s.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_WHITE_SURFACE] = os.path.join(\
                subject_path, "right_white_surface_%s.gii" % subjectname)
        parameters[IntraAnalysis.LEFT_SULCI] = os.path.join(\
                subject_path, "left_sulci_%s.arg" % subjectname)        
        parameters[IntraAnalysis.RIGHT_SULCI] = os.path.join(\
                subject_path, "right_sulci_%s.arg" % subjectname)        
        parameters[IntraAnalysis.LEFT_SULCI_DATA] = os.path.join(\
                subject_path, "left_sulci_%s.data" % subjectname)        
        parameters[IntraAnalysis.RIGHT_SULCI_DATA] = os.path.join(\
                subject_path, "right_sulci_%s.data" % subjectname)        
        parameters[IntraAnalysis.LEFT_LABELED_SULCI] = os.path.join(\
                subject_path, "left_labeled_sulci_%s.arg" % subjectname)        
        parameters[IntraAnalysis.RIGHT_LABELED_SULCI] = os.path.join(\
                subject_path, "right_labeled_sulci_%s.arg" % subjectname) 
        parameters[IntraAnalysis.LEFT_LABELED_SULCI_DATA] = os.path.join(\
                subject_path, "left_labeled_sulci_%s.data" % subjectname)
        parameters[IntraAnalysis.RIGHT_LABELED_SULCI_DATA] = os.path.join(\
                subject_path, "right_labeled_sulci_%s.data" % subjectname) 

        return parameters

    @classmethod
    def create_outputdirs(cls, subject, outputdir):
        group_path = os.path.join(outputdir, subject.groupname)
        create_directory_if_missing(group_path)
        subject_path = os.path.join(group_path, subject.subjectname)
        create_directory_if_missing(subject_path)    


def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


IntraAnalysis._init_class()
