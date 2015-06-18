import os
import glob
import re
import shutil

from morphologist.core.subject import Subject
from morphologist.core.analysis import Analysis, ImportationError
from morphologist.core.utils import create_directory_if_missing, create_directories_if_missing
from morphologist.intra_analysis.steps import \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    GreyWhite, SpatialNormalization, Grey, GreySurface, WhiteSurface, Sulci, \
    SulciLabelling, Morphometry
from morphologist.intra_analysis import constants
from morphologist.intra_analysis.parameters import IntraAnalysisParameterNames

# CAPSUL
from capsul.process.process_with_fom import ProcessWithFom
from capsul.pipeline import pipeline_tools

# CAPSUL morphologist
from morphologist.capsul.morphologist import Morphologist


class IntraAnalysis(Analysis):

    def __init__(self, study):
        super(IntraAnalysis, self).__init__(study)

        self.ACQUISITION = 'default_acquisition'
        self.ANALYSIS = 'default_analysis'
        self.GRAPH_VERSION = '3.1'
        self.FOLDS_SESSION = 'default_session'
        self.MODALITY = 't1mri'

        self.subject = None
        if study.template_pipeline is None:
            study.template_pipeline = self.build_pipeline()
        # share the same instance of the pipeline to save memory and, most of
        # all, instantiation time
        self.pipeline = study.template_pipeline

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
        pipeline = Morphologist()
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

        return ProcessWithFom(pipeline, self.study)

    def import_data(self, subject):
        from capsul.process import get_process_instance
        import_step = get_process_instance(
            'morphologist.capsul.import_t1_mri.ImportT1Mri')

        import_step.input = subject.filename
        import_step.output \
            = self.pipeline.process.t1mri
        import_step.referential = self.pipeline.process. \
            PrepareSubject_TalairachFromNormalization_source_referential
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
        self.create_fom_completion(subject)

    def propagate_parameters(self):
        pipeline_tools.set_pipeline_state_from_dict(
            self.pipeline.process, self.parameters)

    def create_fom_completion(self, subject):
        pipeline = self.pipeline
        attributes_dict = {
            'center': subject.groupname,
            'subject': subject.name,
            'acquisition': self.ACQUISITION,
            'analysis': self.ANALYSIS,
            'graph_version': self.GRAPH_VERSION,
            'sulci_recognition_session': self.FOLDS_SESSION
        }
        do_completion = False
        for attribute, value in attributes_dict.iteritems():
            if pipeline.attributes[attribute] != value:
                pipeline.attributes[attribute] = value
                do_completion = True
        if do_completion:
            #print 'create_completion for:', subject.id()
            pipeline.create_completion()
            self.parameters = pipeline_tools.dump_pipeline_state_as_dict(
                self.pipeline.process)
        #else: print 'skip completion for:', subject.id()

    def clear_results(self, step_ids=None):
        to_remove = self.existing_results(step_ids)
        print 'files to be removed:'
        print to_remove
        for filename in to_remove:
            filenames = self._files_for_format(filename)
            for f in filenames:
                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

    def remove_subject_dir(self):
        self.propagate_parameters()
        t1mri_dir = self.pipeline.process.t1mri
        acquisition_dir = os.path.dirname(t1mri_dir)
        modality_dir = os.path.dirname(acquisition_dir)
        subject_dir = os.path.dirname(modality_dir)
        shutil.rmtree(subject_dir)

    def _files_for_format(self, filename):
        ext_map = {
            'ima': ['ima', 'dim'],
            'img': ['img', 'hdr'],
            'arg': ['arg', 'data'],
        }
        ext_pos = filename.rfind('.')
        if ext_pos < 0:
            return [filename, filename + '.minf']
        ext = filename[ext_pos + 1:]
        exts = ext_map.get(ext, [ext])
        fname_base = filename[:ext_pos + 1]
        return [fname_base + ext for ext in exts] + [filename + '.minf']

    def existing_results(self, step_ids=None):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        pipeline.enable_all_pipeline_steps()
        if step_ids:
            for pstep in pipeline.pipeline_steps.user_traits().keys():
                if pstep not in step_ids:
                    setattr(pipeline.pipeline_steps, pstep, False)
        outputs = pipeline_tools.nodes_with_existing_outputs(
            pipeline, recursive=True, exclude_inputs=True)
        existing = set()
        for node, item_list in outputs.iteritems():
            # WARNING the main input may appear in outputs
            # (reorientation steps)
            existing.update([filename for param, filename in item_list])
        if self.pipeline.process.t1mri in existing:
            existing.remove(self.pipeline.process.t1mri)
        return existing

    def has_some_results(self):
        return bool(self.existing_results())

    def has_all_results(self):
        # here we use the hard-coded outputs list in
        # IntraAnalysisParameterNames since we cannot determine automatically
        # from a pipeline if all outputs are expected or not (many are
        # optional, but still useful in our context)
        pipeline = self.pipeline.process
        for parameter in \
                IntraAnalysisParameterNames.get_output_file_parameter_names():
            value = getattr(pipeline, parameter)
            if not isinstance(value, basestring) or not os.path.exists(value):
                return False
        return True

