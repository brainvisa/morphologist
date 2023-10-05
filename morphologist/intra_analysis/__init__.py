from __future__ import absolute_import
import os
import glob
import re
import shutil

from morphologist.core.subject import Subject
from morphologist.core.analysis import SharedPipelineAnalysis, \
    ImportationError
from morphologist.intra_analysis.steps import \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    GreyWhite, SpatialNormalization, Grey, GreySurface, WhiteSurface, Sulci, \
    SulciLabelling, Morphometry
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames

# CAPSUL
from capsul.pipeline import pipeline_tools
from capsul.schemas.brainvisa import declare_morpho_schemas


declare_morpho_schemas('morphologist.capsul')


class IntraAnalysis(SharedPipelineAnalysis):

    def __init__(self, study):
        '''
        Parameters
        ----------
        stydy: Capsul insance
        '''
        super(IntraAnalysis, self).__init__(study)

        self.ACQUISITION = 'default_acquisition'
        self.ANALYSIS = 'default_analysis'
        self.GRAPH_VERSION = '3.1'
        self.FOLDS_SESSION = 'default_session'
        self.MODALITY = 't1mri'

        self.subject = None

    def _init_steps(self):
        self._steps = [
            SpatialNormalization(),
            BiasCorrection(),
            HistogramAnalysis(),
            BrainSegmentation(),
            SplitBrain(),
            GreyWhite('left'),
            GreyWhite('right'),
            Grey('left'),
            Grey('right'),
            GreySurface('left'),
            GreySurface('right'),
            WhiteSurface('left'),
            WhiteSurface('right'),
            Sulci('left'),
            Sulci('right'),
            SulciLabelling('left'),
            SulciLabelling('right'),
            Morphometry()
        ]

    def build_pipeline(self):
        pipeline = self.study.executable(
            'morphologist.capsul.morphologist.Morphologist')
        # rework steps with finer grain
        pipeline.remove_pipeline_step('grey_white_segmentation')
        pipeline.remove_pipeline_step('white_mesh')
        pipeline.remove_pipeline_step('pial_mesh')
        pipeline.remove_pipeline_step('sulci')
        pipeline.remove_pipeline_step('sulci_labelling')

        pipeline.add_pipeline_step('grey_white_segmentation_left',
                                   ['GreyWhiteClassification'])
        pipeline.add_pipeline_step('grey_white_segmentation_right',
                                   ['GreyWhiteClassification_1'])
        pipeline.add_pipeline_step('grey_white_topology_left',
                                   ['GreyWhiteTopology'])
        pipeline.add_pipeline_step('grey_white_topology_right',
                                   ['GreyWhiteTopology_1'])
        pipeline.add_pipeline_step('white_mesh_left', ['GreyWhiteMesh'])
        pipeline.add_pipeline_step('white_mesh_right', ['GreyWhiteMesh_1'])
        pipeline.add_pipeline_step('pial_mesh_left', ['PialMesh'])
        pipeline.add_pipeline_step('pial_mesh_right', ['PialMesh_1'])
        pipeline.add_pipeline_step('sulci_skeleton_left', ['SulciSkeleton'])
        pipeline.add_pipeline_step('sulci_skeleton_right', ['SulciSkeleton_1'])
        pipeline.add_pipeline_step('sulci_left', ['CorticalFoldsGraph'])
        pipeline.add_pipeline_step('sulci_right', ['CorticalFoldsGraph_1'])
        pipeline.add_pipeline_step('sulci_labelling_left',
                                   ['SulciRecognition'])
        pipeline.add_pipeline_step('sulci_labelling_right',
                                   ['SulciRecognition_1'])
        # listen to config activation and adapt normalization steps
        pipeline.attach_config_activations(self.study)

        return pipeline

    def import_data(self, subject):
        import_step = self.study.executable(
            'morphologist.capsul.import_t1_mri.ImportT1Mri')

        import_step.input = subject.filename
        import_step.output = self.pipeline.t1mri
        import_step.referential = self.pipeline.t1mri_referential
        pipeline_tools.create_output_directories(import_step)
        import_step() # run
        return import_step.output

    #def get_subject_filename(self, subject):
        #format = self.study.volumes_format or "NIFTI"
        #ext = self.study.modules_data.foms["input"].formats[format]
        #return os.path.join(
            #self.study.output_directory, subject.groupname, subject.name,
            #self.MODALITY, self.ACQUISITION, subject.name + "." + ext)

    def set_parameters(self, subject):
        self.subject = subject
        super(IntraAnalysis, self).set_parameters(subject)

    def volume_extension(self):
        format = self.study.volumes_format
        ext_dict = {
            "NIFTI gz": "nii.gz",
            "NIFTI": "nii",
            "GIS": "ima",
            "MINC": "mnc",
        }
        return ext_dict[format]

    def get_attributes(self, subject):
        attributes_dict = {
            'center': subject.groupname,
            'subject': subject.name,
            'acquisition': self.ACQUISITION,
            'analysis': self.ANALYSIS,
            'sulci_graph_version': self.GRAPH_VERSION,
            'sulci_recognition_session': self.FOLDS_SESSION,
            'extension': self.volume_extension(),
        }
        return attributes_dict

    def remove_subject_dir(self):
        self.propagate_parameters()
        t1mri_dir = self.pipeline.t1mri
        acquisition_dir = os.path.dirname(t1mri_dir)
        modality_dir = os.path.dirname(acquisition_dir)
        subject_dir = os.path.dirname(modality_dir)
        if os.path.isdir(subject_dir):
            shutil.rmtree(subject_dir)

    def get_output_file_parameter_names(self):
        # here we use the hard-coded outputs list in
        # IntraAnalysisParameterNames since we cannot determine automatically
        # from a pipeline if all outputs are expected or not (many are
        # optional, but still useful in our context)
        return IntraAnalysisParameterNames.get_output_file_parameter_names()

