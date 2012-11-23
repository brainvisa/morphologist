import os

from morphologist.analysis import Analysis, StepFlow, InputParameters, OutputParameters
from morphologist.analysis import UnknownParameterTemplate
from morphologist.intra_analysis_steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain

class IntraAnalysis(Analysis):
    # TODO: change string by a number
    BRAINVISA_PARAM_TEMPLATE = 'brainvisa'
    DEFAULT_PARAM_TEMPLATE = 'default'
    PARAMETER_TEMPLATES = [BRAINVISA_PARAM_TEMPLATE, DEFAULT_PARAM_TEMPLATE]
    param_template_map = {}

    @classmethod
    def _init_class(cls):
        cls.param_template_map[cls.BRAINVISA_PARAM_TEMPLATE] = \
                        BrainvisaIntraAnalysisParameterTemplate
        cls.param_template_map[cls.DEFAULT_PARAM_TEMPLATE] = \
                        DefaultIntraAnalysisParameterTemplate
  
    def __init__(self):
        super(IntraAnalysis, self).__init__(step_flow=None) 
        self._step_flow = self.create_step_flow()

    def create_step_flow(self):
        return IntraAnalysisStepFlow()

    def set_parameters(self, param_template_id, name, image, outputdir):
        if param_template_id not in self.PARAMETER_TEMPLATES:
            raise UnknownParameterTemplate(param_template_id)

        param_template = self.param_template_map[param_template_id]
        self.input_params = param_template.get_input_params(name, image)
        self.output_params = param_template.get_output_params(name, outputdir)



class IntraAnalysisStepFlow(StepFlow):

    def __init__(self):
        super(IntraAnalysisStepFlow, self).__init__()
        self.create_steps()
        self.input_params = IntraAnalysisParameterTemplate.get_empty_input_params()
        self.output_params = IntraAnalysisParameterTemplate.get_empty_output_params()

    def create_steps(self):
        self._bias_correction = BiasCorrection()
        self._histogram_analysis = HistogramAnalysis()
        self._brain_segmentation = BrainSegmentation()
        self._split_brain = SplitBrain()  
        self._steps = [self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 

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
        self._split_brain.commissure_coordinates = self.input_params.commissure_coordinates
        self._split_brain.bary_factor = self.input_params.bary_factor

        self._split_brain.split_mask = self.output_params.split_mask



class IntraAnalysisParameterTemplate(object):
    input_file_param_names = ['mri', 'commissure_coordinates']
    input_other_param_names = ['erosion_size', 'bary_factor']
    output_file_param_names = ['hfiltered',
                               'white_ridges',
                               'edges',
                               'variance',
                               'mri_corrected',
                               'histo_analysis',
                               'brain_mask',
                               'split_mask']

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

    @classmethod
    def get_input_params(cls, subjectname, img_filename):
        #img_filename should be in path/subjectname/t1mri/default_acquisition
        # TODO raise an exception if it not the case ?
        default_acquisition_path = os.path.dirname(img_filename)
        t1mri_path = os.path.dirname(default_acquisition_path)
        subject = os.path.basename(os.path.dirname(t1mri_path))

        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)

        parameters.mri = img_filename
        parameters.commissure_coordinates = os.path.join(default_acquisition_path, 
                                                   "%s.APC" % subject)
        parameters.erosion_size = 1.8
        parameters.bary_factor = 0.6

        return parameters

    @classmethod
    def get_output_params(cls, subjectname, outputdir):
        # the directory hierarchy in the outputdir will be 
        # subjectname/t1mri/default_acquisition/default_analysis/segmentation
        subject_path = os.path.join(outputdir, subjectname)
        create_directory_if_missing(subject_path)
        
        t1mri_path = os.path.join(subject_path, "t1mri")
        create_directory_if_missing(t1mri_path)
        
        default_acquisition_path = os.path.join(t1mri_path, "default_acquisition")
        create_directory_if_missing(default_acquisition_path)

        default_analysis_path = os.path.join(default_acquisition_path, "default_analysis") 
        create_directory_if_missing(default_analysis_path)
          
        segmentation_path = os.path.join(default_analysis_path, "segmentation")
        create_directory_if_missing(segmentation_path)       
 
        parameters = OutputParameters(cls.output_file_param_names)
        parameters.hfiltered = os.path.join(default_analysis_path, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters.white_ridges = os.path.join(default_analysis_path, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters.edges = os.path.join(default_analysis_path, 
                                            "edges_%s.nii" % subjectname)
        parameters.mri_corrected = os.path.join(default_analysis_path, 
                                            "nobias_%s.nii" % subjectname)
        parameters.variance = os.path.join(default_analysis_path, 
                                            "variance_%s.nii" % subjectname)
        parameters.histo_analysis = os.path.join(default_analysis_path, 
                                            "nobias_%s.han" % subjectname)
        parameters.brain_mask = os.path.join(segmentation_path, 
                                            "brain_%s.nii" % subjectname)
        parameters.split_mask = os.path.join(segmentation_path, 
                                            "voronoi_%s.nii" % subjectname)
        return parameters


class DefaultIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):

    @classmethod
    def get_input_params(cls, subjectname, img_filename):
        parameters = InputParameters(cls.input_file_param_names,
                                     cls.input_other_param_names)

        parameters.mri = img_filename
        mri_dirname = os.path.dirname(img_filename)
        parameters.commissure_coordinates = os.path.join(mri_dirname, 
                                                         "%s.APC" %subjectname)
      
        parameters.erosion_size = 1.8
        parameters.bary_factor = 0.6

        return parameters

    @classmethod
    def get_output_params(cls, subjectname, outputdir):
        parameters = OutputParameters(cls.output_file_param_names)

        subject_dirname = os.path.join(outputdir, subjectname)
        create_directory_if_missing(subject_dirname)    

        parameters.hfiltered = os.path.join(subject_dirname, 
                                            "hfiltered_%s.nii" % subjectname)
        parameters.white_ridges = os.path.join(subject_dirname, 
                                            "whiteridge_%s.nii" % subjectname)
        parameters.edges = os.path.join(subject_dirname, 
                                            "edges_%s.nii" % subjectname)
        parameters.mri_corrected = os.path.join(subject_dirname, 
                                            "nobias_%s.nii" % subjectname)
        parameters.variance = os.path.join(subject_dirname, 
                                            "variance_%s.nii" % subjectname)
        parameters.histo_analysis = os.path.join(subject_dirname, 
                                            "nobias_%s.han" % subjectname)
        parameters.brain_mask = os.path.join(subject_dirname, 
                                            "brain_%s.nii" % subjectname)
        parameters.split_mask = os.path.join(subject_dirname, 
                                            "voronoi_%s.nii" % subjectname)
        return parameters


def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


IntraAnalysis._init_class()
