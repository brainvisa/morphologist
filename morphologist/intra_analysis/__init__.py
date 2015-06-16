import os
import glob
import re
import shutil

from morphologist.core.subject import Subject
from morphologist.core.analysis import Analysis, Parameters, \
                                  ImportationError, ParameterTemplate
from morphologist.core.utils import create_directory_if_missing, create_directories_if_missing
from morphologist.intra_analysis.steps import \
    BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
    GreyWhite, SpatialNormalization, Grey, GreySurface, WhiteSurface, Sulci, \
    SulciLabelling, Morphometry
from morphologist.intra_analysis import constants
from morphologist.intra_analysis.parameters import \
    BrainvisaIntraAnalysisParameterTemplate, \
    IntraAnalysisParameterTemplate, \
    IntraAnalysisParameterNames

# CAPSUL
from capsul.process.process_with_fom import ProcessWithFom
from capsul.pipeline import pipeline_tools

# CAPSUL morphologist
from morphologist.capsul.morphologist import Morphologist


class IntraAnalysis(Analysis):
    PARAMETER_TEMPLATES = [BrainvisaIntraAnalysisParameterTemplate]

    def __init__(self, parameter_template, study):
        super(IntraAnalysis, self).__init__(parameter_template, study)

        self.subject = None
        self.inputs = IntraAnalysisParameterTemplate.get_empty_inputs()
        self.outputs = IntraAnalysisParameterTemplate.get_empty_outputs()
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
            GreyWhite(),
            Grey(),
            GreySurface(),
            WhiteSurface(),
            Sulci(),
            SulciLabelling(),
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

    @classmethod
    def get_default_parameter_template_name(cls):
        return BrainvisaIntraAnalysisParameterTemplate.name

    def import_data(self, subject):
        from capsul.process import get_process_instance
        import_step = get_process_instance(
            'morphologist.capsul.import_t1_mri.ImportT1Mri')

        import_step.input = subject.filename
        import_step.output \
            = self.parameter_template.get_subject_filename(subject)
        import_step.referential = self.pipeline.process. \
            PrepareSubject_TalairachFromNormalization_source_referential
        pipeline_tools.create_output_directories(import_step)
        import_step() # run
        return import_step.output

    def propagate_parameters(self):
        pass
        #self.create_fom_completion()

    def create_fom_completion(self, subject):
        pipeline = self.pipeline
        attributes_dict = {
            'center': subject.groupname,
            'subject': subject.name,
            'acquisition': self.parameter_template.ACQUISITION,
            'analysis': self.parameter_template.ANALYSIS,
            'graph_version': self.parameter_template.GRAPH_VERSION,
            'sulci_recognition_session': self.parameter_template.FOLDS_SESSION
        }
        do_completion = False
        for attribute, value in attributes_dict.iteritems():
            if pipeline.attributes[attribute] != value:
                pipeline.attributes[attribute] = value
                do_completion = True
        if do_completion:
            print 'create_completion for:', subject.id()
            pipeline.create_completion()
        else: print 'skip completion for:', subject.id()

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
        self.create_fom_completion(subject)
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

    #def has_all_results(self):


