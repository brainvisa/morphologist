import os

from corist.image_importation import ImportationError

from morphologist.analysis import Analysis, InputParameters, OutputParameters
from morphologist.intra_analysis_steps import ImageImportation, BiasCorrection, \
                                HistogramAnalysis, BrainSegmentation, SplitBrain, \
                                SpatialNormalization 

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
        self._steps = [self._normalization, 
                       self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 


    @classmethod
    def import_data(cls, parameter_template, filename, subjectname, outputdir):

        import_step = ImageImportation()
        import_step.input = filename
        import_step.output = cls.get_mri_path(parameter_template, 
                                                        subjectname,
                                                        outputdir)
        cls.create_outputdirs(parameter_template, subjectname, outputdir)
        if import_step.run() != 0:
            raise ImportationError()
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


    @classmethod
    def get_mri_path(cls, parameter_template, subjectname, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        return param_template_instance.get_mri_path(subjectname, directory)
    

    @classmethod
    def create_outputdirs(cls, parameter_template, subjectname, directory):
        param_template_instance = cls.param_template_map[parameter_template]
        param_template_instance.create_outputdirs(subjectname, directory)



class IntraAnalysisParameterTemplate(object):
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
                               IntraAnalysis.SPLIT_MASK]

    @classmethod
    def get_empty_input_params(cls):
        return InputParameters(cls.input_file_param_names,
                               cls.input_other_param_names)

    @classmethod
    def get_empty_output_params(cls):
        return OutputParameters(cls.output_file_param_names)

    @classmethod
    def get_input_params(cls, subjectname, img_filename):
        raise Exception("IntraAnalysisParameterTemplate is an abstract class")

    @classmethod
    def get_output_params(cls, subjectname, outputdir):
        raise Exception("IntraAnalysisParameterTemplate is an abstract class")


class BrainvisaIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):

    ACQUISITION = "default_acquisition"
    ANALYSIS = "default_analysis"
    REGISTRATION = "registration"
    MODALITY = "t1mri"
    SEGMENTATION = "segmentation"
    
    @classmethod
    def get_mri_path(cls, subjectname, directory):
        return os.path.join(directory, subjectname, cls.MODALITY, 
                            cls.ACQUISITION, subjectname + ".nii")

    @classmethod
    def get_input_params(cls, subjectname, img_filename):
        #img_filename should be in path/subjectname/t1mri/default_acquisition
        # TODO raise an exception if it not the case ?
        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)

        parameters[IntraAnalysis.MRI] = img_filename

        parameters[IntraAnalysis.EROSION_SIZE] = 1.8
        parameters[IntraAnalysis.BARY_FACTOR] = 0.6

        return parameters

    @classmethod
    def get_output_params(cls, subjectname, outputdir):
        # the directory hierarchy in the outputdir will be 
        # subjectname/t1mri/default_acquisition/default_analysis/segmentation
        default_acquisition_path = os.path.join(outputdir, subjectname, 
                                                   cls.MODALITY, cls.ACQUISITION)
        registration_path = os.path.join(default_acquisition_path, cls.REGISTRATION)
        default_analysis_path = os.path.join(default_acquisition_path, cls.ANALYSIS) 
          
        segmentation_path = os.path.join(default_analysis_path, cls.SEGMENTATION)
 
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
        return parameters

    @classmethod
    def create_outputdirs(cls, subjectname, outputdir):
        subject_path = os.path.join(outputdir, subjectname)
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

           
class DefaultIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):

    @classmethod
    def get_mri_path(cls, subjectname, directory):
        return os.path.join(directory, subjectname, subjectname + ".nii")

    @classmethod
    def get_input_params(cls, subjectname, img_filename):
        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)

        parameters[IntraAnalysis.MRI] = img_filename
      
        parameters[IntraAnalysis.EROSION_SIZE] = 1.8
        parameters[IntraAnalysis.BARY_FACTOR] = 0.6

        return parameters

    @classmethod
    def get_output_params(cls, subjectname, outputdir):
        parameters = OutputParameters(cls.output_file_param_names)

        subject_dirname = os.path.join(outputdir, subjectname)
        parameters[IntraAnalysis.COMMISSURE_COORDINATES] = os.path.join(subject_dirname, 
                                                         "%s.APC" %subjectname)
        parameters[IntraAnalysis.TALAIRACH_TRANSFORMATION] = os.path.join(subject_dirname,
                                                            "RawT1-%s_TO_Talairach-ACPC.trm" 
                                                            % subjectname)
        parameters[IntraAnalysis.HFILTERED] = os.path.join(subject_dirname, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters[IntraAnalysis.WHITE_RIDGES] = os.path.join(subject_dirname, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters[IntraAnalysis.EDGES] = os.path.join(subject_dirname, 
                                            "edges_%s.nii" % subjectname)
        parameters[IntraAnalysis.CORRECTED_MRI] = os.path.join(subject_dirname, 
                                            "nobias_%s.nii" % subjectname)
        parameters[IntraAnalysis.VARIANCE] = os.path.join(subject_dirname, 
                                            "variance_%s.nii" % subjectname)
        parameters[IntraAnalysis.HISTO_ANALYSIS] = os.path.join(subject_dirname, 
                                            "nobias_%s.han" % subjectname)
        parameters[IntraAnalysis.BRAIN_MASK] = os.path.join(subject_dirname, 
                                            "brain_%s.nii" % subjectname)
        parameters[IntraAnalysis.SPLIT_MASK] = os.path.join(subject_dirname, 
                                            "voronoi_%s.nii" % subjectname)
        return parameters

    @classmethod
    def create_outputdirs(cls, subjectname, outputdir):
        subject_dirname = os.path.join(outputdir, subjectname)
        create_directory_if_missing(subject_dirname)    


def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


IntraAnalysis._init_class()
