import os

from morphologist.analysis import Analysis, StepFlow, InputParameters, OutputParameters
from morphologist.steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain
from morphologist.analysis import UnknownParameterTemplate


class IntraAnalysis(Analysis):

    BRAINVISA_PARAM_TEMPLATE = 'brainvisa'
    DEFAULT_PARAM_TEMPLATE = 'default'
    PARAMETER_TEMPLATES = ['brainvisa', 'default']
  

    def __init__(self):
        step_flow = IntraAnalysisStepFlow()
        super(IntraAnalysis, self).__init__(step_flow) 
 

    def set_parameters(self, parameter_template, name, image, outputdir):

        if parameter_template not in IntraAnalysis.PARAMETER_TEMPLATES:
            raise UnknownParameterTemplate(parameter_template) 

        if parameter_template == IntraAnalysis.BRAINVISA_PARAM_TEMPLATE:
            self.input_params = IntraAnalysisInputParameters.from_brainvisa_template(image)
            self.output_params = IntraAnalysisOutputParameters.from_brainvisa_template(outputdir, 
                                                                                       name)
        elif parameter_template == IntraAnalysis.DEFAULT_PARAM_TEMPLATE:
            self.input_params = IntraAnalysisInputParameters.from_default_template(name, 
                                                                                  image)
            self.output_params = IntraAnalysisOutputParameters.from_default_template(outputdir,
                                                                                   name)

class IntraAnalysisStepFlow(StepFlow):

    def __init__(self):
        super(IntraAnalysisStepFlow, self).__init__()
        self._bias_correction = BiasCorrection()
        self._histogram_analysis = HistogramAnalysis()
        self._brain_segmentation = BrainSegmentation()
        self._split_brain = SplitBrain()  
        self._steps = [self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 

        self.input_params = IntraAnalysisInputParameters() 

        self.output_params = IntraAnalysisOutputParameters()


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


class IntraAnalysisInputParameters(InputParameters):
    
    def __init__(self):
        file_param_names = ['mri',
                            'commissure_coordinates']
        other_param_names = ['erosion_size',
                             'bary_factor']
        super(IntraAnalysisInputParameters, self).__init__(file_param_names, 
                                                           other_param_names)

    @classmethod
    def from_brainvisa_template(cls, img_file_path):
        #img_file_path should be in path/subject_name/t1mri/default_acquisition
        # TODO raise an exception if it not the case ?
        default_acquisition_path = os.path.dirname(img_file_path)
        t1mri_path = os.path.dirname(default_acquisition_path)
        subject = os.path.basename(os.path.dirname(t1mri_path))

        parameters = cls()

        parameters.mri = img_file_path
        parameters.commissure_coordinates = os.path.join(default_acquisition_path, 
                                                   "%s.APC" % subject)
        parameters.erosion_size = 1.8
        parameters.bary_factor = 0.6

        return parameters

    @classmethod
    def from_default_template(cls, subject_name, img_file_path):
        parameters = cls()

        parameters.mri = img_file_path
        mri_dirname = os.path.dirname(img_file_path)
        parameters.commissure_coordinates = os.path.join(mri_dirname, 
                                                         "%s.APC" %subject_name)
      
        parameters.erosion_size = 1.8
        parameters.bary_factor = 0.6

        return parameters



class IntraAnalysisOutputParameters(OutputParameters):

    def __init__(self):
        file_param_names =  ['hfiltered',
                             'white_ridges',
                             'edges',
                             'variance',
                             'mri_corrected',
                             'histo_analysis',
                             'brain_mask',
                             'split_mask']
        super(IntraAnalysisOutputParameters, self).__init__(file_param_names)

    @classmethod
    def from_brainvisa_template(cls, output_dir, subject_name):
        # the directory hierarchy in the output_dir will be 
        # subject_name/t1mri/default_acquisition/default_analysis/segmentation
        
        subject_path = os.path.join(output_dir, subject_name)
        create_directory_if_missing(subject_path)
        
        t1mri_path = os.path.join(subject_path, "t1mri")
        create_directory_if_missing(t1mri_path)
        
        default_acquisition_path = os.path.join(t1mri_path, "default_acquisition")
        create_directory_if_missing(default_acquisition_path)

        default_analysis_path = os.path.join(default_acquisition_path, "default_analysis") 
        create_directory_if_missing(default_analysis_path)
          
        segmentation_path = os.path.join(default_analysis_path, "segmentation")
        create_directory_if_missing(segmentation_path)       
 
        parameters = cls()
        parameters.hfiltered = os.path.join(default_analysis_path, 
                                            "hfiltered_%s.ima" % subject_name)
        parameters.white_ridges = os.path.join(default_analysis_path, 
                                            "whiteridge_%s.ima" % subject_name)
        parameters.edges = os.path.join(default_analysis_path, 
                                            "edges_%s.ima" % subject_name)
        parameters.mri_corrected = os.path.join(default_analysis_path, 
                                            "nobias_%s.ima" % subject_name)
        parameters.variance = os.path.join(default_analysis_path, 
                                            "variance_%s.ima" % subject_name)
        parameters.histo_analysis = os.path.join(default_analysis_path, 
                                            "nobias_%s.han" % subject_name)
        parameters.brain_mask = os.path.join(segmentation_path, 
                                            "brain_%s.ima" % subject_name)
        parameters.split_mask = os.path.join(segmentation_path, 
                                            "voronoi_%s.ima" % subject_name)
        return parameters

    @classmethod
    def from_default_template(cls, output_dir, subject_name):
        parameters = cls()

        subject_dirname = os.path.join(output_dir, subject_name)
        create_directory_if_missing(subject_dirname)    

        parameters.hfiltered = os.path.join(subject_dirname, 
                                            "hfiltered_%s.ima" % subject_name)
        parameters.white_ridges = os.path.join(subject_dirname, 
                                            "whiteridge_%s.ima" % subject_name)
        parameters.edges = os.path.join(subject_dirname, 
                                            "edges_%s.ima" % subject_name)
        parameters.mri_corrected = os.path.join(subject_dirname, 
                                            "nobias_%s.ima" % subject_name)
        parameters.variance = os.path.join(subject_dirname, 
                                            "variance_%s.ima" % subject_name)
        parameters.histo_analysis = os.path.join(subject_dirname, 
                                            "nobias_%s.han" % subject_name)
        parameters.brain_mask = os.path.join(subject_dirname, 
                                            "brain_%s.ima" % subject_name)
        parameters.split_mask = os.path.join(subject_dirname, 
                                            "voronoi_%s.ima" % subject_name)


        return parameters



def create_directory_if_missing(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


