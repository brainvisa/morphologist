import os

from morphologist.analysis import Analysis, InputParameters, OutputParameters, \
                                  ImportationError, ParameterTemplate
from morphologist.intra_analysis_steps import ImageImportation, \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    LeftGreyWhite, RightGreyWhite, SpatialNormalization, Grey, WhiteSurface


class IntraAnalysis(Analysis):
    # TODO: change string by a number
    BRAINVISA_PARAM_TEMPLATE = 'brainvisa'
    DEFAULT_PARAM_TEMPLATE = 'default'
    PARAMETER_TEMPLATES = [BRAINVISA_PARAM_TEMPLATE, DEFAULT_PARAM_TEMPLATE]
    param_template_map = {}

    MRI = 'mri'
    COMMISSURE_COORDINATES = 'commissure_coordinates'
    TALAIRACH_TRANSFORMATION = 'talairach_transformation'
    EROSION_SIZE = 'erosion_size' 
    BARY_FACTOR = 'bary_factor'
    HFILTERED = 'hfiltered'
    WHITE_RIDGES = 'white_ridges'
    EDGES = 'edges'
    VARIANCE = 'variance'
    CORRECTED_MRI = 'corrected_mri'
    HISTO_ANALYSIS = 'histo_analysis'
    BRAIN_MASK = 'brain_mask'
    SPLIT_MASK = 'split_mask'
    LEFT_GREY_WHITE = 'left_grey_white'
    RIGHT_GREY_WHITE = 'right_grey_white'
    LEFT_GREY = 'left_grey'
    RIGHT_GREY = 'right_grey'
    LEFT_WHITE_SURFACE = 'left_white_surface'
    RIGHT_WHITE_SURFACE = 'right_white_surface'

    # TODO: reimplement a standard python method ?
    @classmethod
    def _init_class(cls):
        cls.param_template_map[cls.BRAINVISA_PARAM_TEMPLATE] = \
                        BrainvisaIntraAnalysisParameterTemplate
        cls.param_template_map[cls.DEFAULT_PARAM_TEMPLATE] = \
                        DefaultIntraAnalysisParameterTemplate
  
    def __init__(self):
        super(IntraAnalysis, self).__init__() 
        self._init_steps()
        self.input_params = IntraAnalysisParameterTemplate.get_empty_input_params()
        self.output_params = IntraAnalysisParameterTemplate.get_empty_output_params()

    def _init_steps(self):
        self._normalization = SpatialNormalization()
        self._bias_correction = BiasCorrection()
        self._histogram_analysis = HistogramAnalysis()
        self._brain_segmentation = BrainSegmentation()
        self._split_brain = SplitBrain()
        self._left_grey_white = LeftGreyWhite()
        self._right_grey_white = RightGreyWhite()
        self._left_grey = Grey()
        self._right_grey = Grey()
        self._left_white_surface = WhiteSurface()
        self._right_white_surface = WhiteSurface()
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

        import_step = ImageImportation()
        import_step.input = filename
        import_step.output = cls.get_mri_path(parameter_template,
                                              groupname, 
                                              subjectname,
                                              outputdir)
        cls.create_outputdirs(parameter_template, groupname, subjectname, outputdir)
        if import_step.run() != 0:
            raise ImportationError("The importation failed for the subject %s."
                                   % subjectname)
        return import_step.output

    def propagate_parameters(self):
        self._normalization.mri = self.input_params[IntraAnalysis.MRI]
        self._normalization.commissure_coordinates = self.output_params[IntraAnalysis.COMMISSURE_COORDINATES]
        self._normalization.talairach_transformation = self.output_params[IntraAnalysis.TALAIRACH_TRANSFORMATION]
        
        self._bias_correction.mri = self.input_params[IntraAnalysis.MRI]
        self._bias_correction.commissure_coordinates = self._normalization.commissure_coordinates

        self._bias_correction.hfiltered = self.output_params[IntraAnalysis.HFILTERED]
        self._bias_correction.white_ridges = self.output_params[IntraAnalysis.WHITE_RIDGES]
        self._bias_correction.edges = self.output_params[IntraAnalysis.EDGES]
        self._bias_correction.variance = self.output_params[IntraAnalysis.VARIANCE]
        self._bias_correction.corrected_mri = self.output_params[IntraAnalysis.CORRECTED_MRI]


        self._histogram_analysis.corrected_mri = self._bias_correction.corrected_mri
        self._histogram_analysis.hfiltered = self._bias_correction.hfiltered
        self._histogram_analysis.white_ridges = self._bias_correction.white_ridges
        
        self._histogram_analysis.histo_analysis = self.output_params[IntraAnalysis.HISTO_ANALYSIS]


        self._brain_segmentation.corrected_mri = self._bias_correction.corrected_mri
        self._brain_segmentation.commissure_coordinates = self._normalization.commissure_coordinates
        self._brain_segmentation.white_ridges = self._bias_correction.white_ridges
        self._brain_segmentation.edges = self._bias_correction.edges
        self._brain_segmentation.variance = self._bias_correction.variance
        self._brain_segmentation.histo_analysis = self._histogram_analysis.histo_analysis        
        self._brain_segmentation.erosion_size = self.input_params[IntraAnalysis.EROSION_SIZE]

        self._brain_segmentation.brain_mask = self.output_params[IntraAnalysis.BRAIN_MASK]

  
        self._split_brain.corrected_mri = self._bias_correction.corrected_mri
        self._split_brain.brain_mask = self._brain_segmentation.brain_mask
        self._split_brain.white_ridges = self._bias_correction.white_ridges
        self._split_brain.histo_analysis = self._histogram_analysis.histo_analysis
        self._split_brain.commissure_coordinates = self._normalization.commissure_coordinates
        self._split_brain.bary_factor = self.input_params[IntraAnalysis.BARY_FACTOR]

        self._split_brain.split_mask = self.output_params[IntraAnalysis.SPLIT_MASK]


        self._left_grey_white.corrected_mri = self._bias_correction.corrected_mri
        self._left_grey_white.commissure_coordinates = self._normalization.commissure_coordinates
        self._left_grey_white.histo_analysis = self._histogram_analysis.histo_analysis
        self._left_grey_white.split_mask = self._split_brain.split_mask
        self._left_grey_white.edges = self._bias_correction.edges
        self._left_grey_white.left_grey_white = self.output_params[IntraAnalysis.LEFT_GREY_WHITE]

        self._right_grey_white.corrected_mri = self._bias_correction.corrected_mri
        self._right_grey_white.commissure_coordinates = self._normalization.commissure_coordinates
        self._right_grey_white.histo_analysis = self._histogram_analysis.histo_analysis
        self._right_grey_white.split_mask = self._split_brain.split_mask
        self._right_grey_white.edges = self._bias_correction.edges
        self._right_grey_white.right_grey_white = self.output_params[IntraAnalysis.RIGHT_GREY_WHITE]


        self._left_grey.corrected_mri = self._bias_correction.corrected_mri
        self._left_grey.histo_analysis = self._histogram_analysis.histo_analysis
        self._left_grey.grey_white = self._left_grey_white.left_grey_white
        self._left_grey.grey = self.output_params[IntraAnalysis.LEFT_GREY]

        self._right_grey.corrected_mri = self._bias_correction.corrected_mri
        self._right_grey.histo_analysis = self._histogram_analysis.histo_analysis
        self._right_grey.grey_white = self._right_grey_white.right_grey_white
        self._right_grey.grey = self.output_params[IntraAnalysis.RIGHT_GREY]

        self._left_white_surface.grey = self._left_grey.grey
        self._left_white_surface.white_surface = self.output_params[IntraAnalysis.LEFT_WHITE_SURFACE]

        self._right_white_surface.grey = self._right_grey.grey
        self._right_white_surface.white_surface = self.output_params[IntraAnalysis.RIGHT_WHITE_SURFACE]

    @classmethod
    def get_mri_path(cls, parameter_template, groupname, subjectname, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        return param_template_instance.get_mri_path(groupname, subjectname, directory)
    
    @classmethod
    def create_outputdirs(cls, parameter_template, groupname, subjectname, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        param_template_instance.create_outputdirs(groupname, subjectname, directory)


class IntraAnalysisParameterTemplate(ParameterTemplate):
    input_file_param_names = [IntraAnalysis.MRI]
    input_other_param_names = [IntraAnalysis.EROSION_SIZE, IntraAnalysis.BARY_FACTOR]
    output_file_param_names = [IntraAnalysis.COMMISSURE_COORDINATES,
                               IntraAnalysis.TALAIRACH_TRANSFORMATION,
                               IntraAnalysis.HFILTERED,
                               IntraAnalysis.WHITE_RIDGES,
                               IntraAnalysis.EDGES,
                               IntraAnalysis.VARIANCE,
                               IntraAnalysis.CORRECTED_MRI,
                               IntraAnalysis.HISTO_ANALYSIS,
                               IntraAnalysis.BRAIN_MASK,
                               IntraAnalysis.SPLIT_MASK,
                               IntraAnalysis.LEFT_GREY_WHITE,
                               IntraAnalysis.RIGHT_GREY_WHITE,
                               IntraAnalysis.LEFT_GREY,
                               IntraAnalysis.RIGHT_GREY,
                               IntraAnalysis.LEFT_WHITE_SURFACE,
                               IntraAnalysis.RIGHT_WHITE_SURFACE]

    @classmethod
    def get_empty_input_params(cls):
        return InputParameters(cls.input_file_param_names,
                               cls.input_other_param_names)

    @classmethod
    def get_empty_output_params(cls):
        return OutputParameters(cls.output_file_param_names)
    
    @classmethod
    def get_mri_path(cls, groupname, subjectname, directory):
        raise Exception("IntraAnalysisParameterTemplate is an Abstract class.")
    
    @classmethod
    def get_input_params(cls, input_filename):
        # input_filename should be in cls.get_mri_path()
        # TODO raise an exception if it not the case ?
        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)
        parameters[IntraAnalysis.MRI] = input_filename
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
    
    @classmethod
    def get_mri_path(cls, groupname, subjectname, directory):
        return os.path.join(directory, groupname, subjectname, cls.MODALITY, 
                            cls.ACQUISITION, subjectname + ".nii")

    @classmethod
    def get_output_params(cls, groupname, subjectname, outputdir):
        # the directory hierarchy in the outputdir will be 
        # subjectname/t1mri/default_acquisition/default_analysis/segmentation
        default_acquisition_path = os.path.join(outputdir, groupname, subjectname, 
                                                   cls.MODALITY, cls.ACQUISITION)
        registration_path = os.path.join(default_acquisition_path, cls.REGISTRATION)
        default_analysis_path = os.path.join(default_acquisition_path, cls.ANALYSIS) 
          
        segmentation_path = os.path.join(default_analysis_path, cls.SEGMENTATION)
        surface_path = os.path.join(segmentation_path, cls.SURFACE)
 
        parameters = OutputParameters(cls.output_file_param_names)
        parameters[IntraAnalysis.COMMISSURE_COORDINATES] = os.path.join(default_acquisition_path, 
                                                   "%s.APC" % subjectname)
        parameters[IntraAnalysis.TALAIRACH_TRANSFORMATION] = os.path.join(registration_path, 
                                                         "RawT1-%s_%s_TO_Talairach-ACPC.trm" 
                                                         % (subjectname, cls.ACQUISITION))
        parameters[IntraAnalysis.HFILTERED] = os.path.join(default_analysis_path, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters[IntraAnalysis.WHITE_RIDGES] = os.path.join(default_analysis_path, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.EDGES] = os.path.join(default_analysis_path, 
                                            "edges_%s.nii" % subjectname)
        parameters[IntraAnalysis.CORRECTED_MRI] = os.path.join(default_analysis_path, 
                                            "nobias_%s.nii" % subjectname)
        parameters[IntraAnalysis.VARIANCE] = os.path.join(default_analysis_path, 
                                            "variance_%s.nii" % subjectname)
        parameters[IntraAnalysis.HISTO_ANALYSIS] = os.path.join(default_analysis_path, 
                                            "nobias_%s.han" % subjectname)
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
        parameters[IntraAnalysis.LEFT_WHITE_SURFACE] = os.path.join(\
                        surface_path, "%s_Lwhite.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_WHITE_SURFACE] = os.path.join(\
                        surface_path, "%s_Rwhite.gii" % subjectname)

        return parameters

    @classmethod
    def create_outputdirs(cls, groupname, subjectname, outputdir):
        group_path = os.path.join(outputdir, groupname)
        create_directory_if_missing(group_path)
        
        subject_path = os.path.join(group_path, subjectname)
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

           
class DefaultIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):

    @classmethod
    def get_mri_path(cls, groupname, subjectname, directory):
        return os.path.join(directory, groupname, subjectname, subjectname + ".nii")

    @classmethod
    def get_output_params(cls, groupname, subjectname, outputdir):
        parameters = OutputParameters(cls.output_file_param_names)

        subject_path = os.path.join(outputdir, groupname, subjectname)
        parameters[IntraAnalysis.COMMISSURE_COORDINATES] = os.path.join(subject_path, 
                                                         "%s.APC" %subjectname)
        parameters[IntraAnalysis.TALAIRACH_TRANSFORMATION] = os.path.join(subject_path,
                                                            "RawT1-%s_TO_Talairach-ACPC.trm" 
                                                            % subjectname)
        parameters[IntraAnalysis.HFILTERED] = os.path.join(subject_path, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters[IntraAnalysis.WHITE_RIDGES] = os.path.join(subject_path, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.EDGES] = os.path.join(subject_path, 
                                            "edges_%s.nii" % subjectname)
        parameters[IntraAnalysis.CORRECTED_MRI] = os.path.join(subject_path, 
                                            "nobias_%s.nii" % subjectname)
        parameters[IntraAnalysis.VARIANCE] = os.path.join(subject_path, 
                                            "variance_%s.nii" % subjectname)
        parameters[IntraAnalysis.HISTO_ANALYSIS] = os.path.join(subject_path, 
                                            "nobias_%s.han" % subjectname)
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
        parameters[IntraAnalysis.LEFT_WHITE_SURFACE] = os.path.join(\
                subject_path, "left_white_surface_%s.gii" % subjectname)
        parameters[IntraAnalysis.RIGHT_WHITE_SURFACE] = os.path.join(\
                subject_path, "right_white_surface_%s.gii" % subjectname)

        return parameters

    @classmethod
    def create_outputdirs(cls, groupname, subjectname, outputdir):
        group_path = os.path.join(outputdir, groupname)
        create_directory_if_missing(group_path)
        subject_path = os.path.join(group_path, subjectname)
        create_directory_if_missing(subject_path)    


def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


IntraAnalysis._init_class()
