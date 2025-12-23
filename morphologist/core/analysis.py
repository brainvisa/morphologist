from __future__ import print_function

from __future__ import absolute_import
import copy
import os
import shutil
import traits.api as traits
import sys
import six

from morphologist.core.utils import OrderedDict
# CAPSUL
from capsul.pipeline import pipeline_tools
from capsul.attributes.completion_engine import ProcessCompletionEngine
# AIMS
from soma import aims

class AnalysisFactory(object):
    _registered_analyses = {}

    @classmethod
    def register_analysis(cls, analysis_type, analysis_class):
        cls._registered_analyses[analysis_type] = analysis_class

    @classmethod
    def create_analysis(cls, analysis_type, study):
        analysis_cls = cls.get_analysis_cls(analysis_type) 
        return analysis_cls(study)

    @classmethod
    def get_analysis_cls(cls, analysis_type):
        try:
            analysis_class = cls._registered_analyses[analysis_type]
            return analysis_class
        except KeyError:
            raise UnknownAnalysisError(analysis_type)


class UnknownAnalysisError(Exception):
    pass


class AnalysisMetaClass(type):

    def __init__(cls, name, bases, dct):
        AnalysisFactory.register_analysis(name, cls)
        super(AnalysisMetaClass, cls).__init__(name, bases, dct)


class Analysis(six.with_metaclass(AnalysisMetaClass, object)):
    # XXX the metaclass automatically registers the Analysis class in the
    # AnalysisFactory and initializes the param_template_map

    def __init__(self, study):
        self._init_steps()
        self._init_step_ids()
        self.study = study
        self.pipeline = None
        self.parameters = None

    def _init_steps(self):
        raise NotImplementedError("Analysis is an Abstract class.") 

    def _init_step_ids(self):
        self._step_ids = OrderedDict()
        for i, step in enumerate(self._steps):
            step_id = step.name  ##"%d_%s" % (i, step.name)
            self._step_ids[step_id] = step

    def step_from_id(self, step_id):
        return self._step_ids.get(step_id)

    def import_data(self, subject):
        raise NotImplementedError("Analysis is an Abstract class. import_data must be redefined.")

    def set_parameters(self, subject):
        raise NotImplementedError("Analysis is an Abstract class. set_parameters must be redefined.")

    def propagate_parameters(self):
        raise NotImplementedError("Analysis is an Abstract class. propagate_parameter must be redefined.") 

    def list_input_parameters_with_existing_files(self):
        raise NotImplementedError("Analysis is an Abstract class. list_input_parameters_with_existing_files must be redefined.")

    def list_output_parameters_with_existing_files(self):
        raise NotImplementedError("Analysis is an Abstract class. list_output_parameters_with_existing_files must be redefined.")

    def has_some_results(self, step_ids=None):
        raise NotImplementedError("Analysis is an Abstract class. has_some_results must be redefined.")

    def has_all_results(self, step_ids=None):
        raise NotImplementedError("Analysis is an Abstract class. has_all_results must be redefined.")

    def existing_results(self, step_ids=None):
        raise NotImplementedError("Analysis is an Abstract class. existing_results must be redefined.")

    def clear_results(self, step_ids=None):
        to_remove = self.existing_results(step_ids)
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

    def convert_from_formats(self, old_volumes_format, old_meshes_format):
        # TODO: use aims/somaio IO system for formats extensions
        exts = [['.nii'], ['.nii.gz'], ['.img', '.hdr'], ['.ima', '.dim'],
                ['.dcm'], ['.mnc'],
                ['.gii'], ['.mesh'], ['.ply']]
        vol_formats = ['.nii', '.nii.gz', '.img', '.ima', '.dcm', '.mnc']
        mesh_formats = ['.gii', '.mesh', '.ply']

        def _convert_data(old_name, new_name):
            print('converting:', old_name, 'to:', new_name)
            data = aims.read(old_name)
            aims.write(data, new_name)

        def _remove_data(name):
            for fexts in exts:
                for ext in fexts:
                    if name.endswith(ext):
                        basename =  name[:-len(ext)]
                        real_exts = fexts + [fexts[0] + '.minf']
                        for cext in real_exts:
                            filename = basename + cext
                            if os.path.isdir(filename):
                                print('rmtree', filename)
                                shutil.rmtree(filename)
                            elif os.path.exists(filename):
                                print('rm', filename)
                                os.unlink(filename)

        def _look_for_other_formats(value, new_value):
            old_format = [fext[0] for fext in exts
                          if value.endswith(fext[0])]
            if len(old_format) == 0:
                return value
            old_format = old_format[0]
            if old_format in vol_formats:
                dtype = 0
            elif old_format in mesh_formats:
                dtype = 1
            else:
                return value
            typed_formats = [vol_formats, mesh_formats]

            old_base = value[:-len(old_format)]
            for fexts in exts:
                if not fexts[0] in typed_formats[dtype]:
                    continue
                if not isinstance(new_value, six.string_types) \
                        or not new_value.endswith(fexts[0]):
                    for ext in fexts:
                        new_old_value = old_base + ext
                        if not os.path.exists(new_old_value):
                            # not OK
                            break
                    else:
                        # found matching format
                        return old_base + fexts[0]
            return value

        print('convert analysis', self.subject, 'from formats:',
              old_volumes_format, old_meshes_format, 'to:',
              self.study.volumes_format, self.study.meshes_format)
        #if old_volumes_format == self.study.volumes_format \
                #and old_meshes_format == self.study.meshes_format:
            #print('    nothing to do.')
            #return
        old_params = self.parameters
        # force re-running FOM
        self.set_parameters(self.subject)
        todo = [(old_params, self.parameters)]
        while todo:
            old_dict, new_dict = todo.pop(0)
            old_state = old_dict.get('state', {})
            new_state = new_dict.get('state', {})
            for key, value in six.iteritems(old_state):
                if isinstance(value, six.string_types):
                    new_value = new_state.get(key)
                    if not os.path.exists(value) \
                            and (not isinstance(new_value, six.string_types)
                                 or not os.path.exists(new_value)):
                        value = _look_for_other_formats(value, new_value)
                    if os.path.exists(value):
                        if new_value not in ('', None, traits.Undefined) \
                                and new_value != value:
                            _convert_data(value, new_value)
                        if new_value != value:
                            _remove_data(value)
            old_nodes = old_dict.get('nodes', {})
            new_nodes = new_dict.get('nodes', {})
            if old_nodes:
                todo += [(node, new_nodes.get(key, {}))
                         for key, node in six.iteritems(old_nodes)]


class SharedPipelineAnalysis(Analysis):
    '''
    An Analysis containing a capsul Pipeline instance, shared with other
    Analysis instances in the same study. The pipeline has a
    ProcessCompletionEngine.
    '''

    def __init__(self, study):
        super(SharedPipelineAnalysis, self).__init__(study)
        if study.template_pipeline is None:
            study.template_pipeline = self.build_pipeline()
        completion_model = ProcessCompletionEngine.get_completion_engine(
            study.template_pipeline)
        # share the same instance of the pipeline to save memory and, most of
        # all, instantiation time
        self.pipeline = study.template_pipeline

    def build_pipeline(self):
        '''
        Returns
        -------
        pipeline: Pipeline instance
        '''
        raise NotImplementedError("SharedPipelineAnalysis is an Abstract class. build_pipeline must be redefined.")

    def set_parameters(self, subject):
        self.complete_parameters(subject)

    def propagate_parameters(self):
        if hasattr(self.pipeline, 'current_subject_id') \
                and self.pipeline.current_subject_id \
                    == self.subject.id():
            # OK this is already done.
            return
        pipeline_tools.set_pipeline_state_from_dict(
            self.pipeline, self.parameters)
        self.pipeline.current_subject_id = self.subject.id()

    def get_attributes(self, subject):
        raise NotImplementedError("SharedPipelineAnalysis is an Abstract class. get_attributes must be redefined.")

    def complete_parameters_lowlevel(self, subject):
        pipeline = self.pipeline
        if hasattr(pipeline, 'current_subject_id') \
                and pipeline.current_subject_id \
                    == self.subject.id():
            # OK this is already done.
            return
        attributes_dict = self.get_attributes(subject)
        if not attributes_dict:
            raise AttributeError('Subject %s/%s has no attributes'
                % (subject.groupname, subject.name))
        attributes = pipeline.completion_engine.get_attribute_values() \
            .export_to_dict()
        for attribute, value in six.iteritems(attributes_dict):
            if attributes[attribute] != value:
                attributes[attribute] = value
                #do_completion = True
        # FIXME: only if do_completion ?
        #print 'create_completion for:', subject.id()
        pipeline.completion_engine.complete_parameters(
            {'capsul_attributes': attributes})

    def complete_parameters(self, subject):
        self.complete_parameters_lowlevel(subject)
        self.parameters = pipeline_tools.dump_pipeline_state_as_dict(
            self.pipeline)
        # mark this subject as the one with the current parameters.
        self.pipeline.current_subject_id = subject.id()

    def existing_results(self, step_ids=None):
        pipeline = self.pipeline
        self.propagate_parameters()
        pipeline.enable_all_pipeline_steps()
        if step_ids:
            for pstep in pipeline.pipeline_steps.user_traits().keys():
                if pstep not in step_ids:
                    setattr(pipeline.pipeline_steps, pstep, False)
        outputs = pipeline_tools.nodes_with_existing_outputs(
            pipeline, recursive=True, exclude_inputs=True)
        existing = set()
        for node, item_list in six.iteritems(outputs):
            existing.update([filename for param, filename in item_list])
        # WARNING inputs may appear in outputs
        # (reorientation steps)
        for param_name, trait in six.iteritems(pipeline.user_traits()):
            if not trait.output:
                value = getattr(pipeline, param_name)
                if isinstance(value, six.string_types) and value in existing:
                    existing.remove(value)
        return existing

    def has_some_results(self, step_ids=None):
        return bool(self.existing_results(step_ids=step_ids))

    def list_input_parameters_with_existing_files(self):
        pipeline = self.pipeline
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in six.iteritems(pipeline.user_traits())
                       if not trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, six.string_types) and os.path.exists(value):
                params[param_name] = value

        return params

    def list_output_parameters_with_existing_files(self):
        pipeline = self.pipeline
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in six.iteritems(pipeline.user_traits())
                       if trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, six.string_types) and os.path.exists(value):
                params[param_name] = value
        return params

        #existing =  pipeline_tools.nodes_with_existing_outputs(
            #self.pipeline)
        #params = []
        #for node_name, values in  six.iteritems(existing):
            #parmams.update(dict(values))
        #return params

    def is_parameter_in_steps(self, param_name, step_ids=None):
        if step_ids is None:
            return True
        pipeline = self.pipeline
        plug = pipeline.pipeline_node.plugs[param_name]
        steps_nodes = set()
        for step_id, trait \
                in six.iteritems(pipeline.pipeline_steps.user_traits()):
            if step_id in step_ids:
                steps_nodes.update(trait.nodes)
        if plug.output:
            links = plug.links_from
        else:
            links = plug.links_to
        # TODO: propagate through switches
        for link in links:
            node = link[2]
            if node in steps_nodes:
                return True
        return False

    def get_output_file_parameter_names(self):
        # here we use the hard-coded outputs list in
        # IntraAnalysisParameterNames since we cannot determine automatically
        # from a pipeline if all outputs are expected or not (many are
        # optional, but still useful in our context)
        raise NotImplementedError("SharedPipelineAnalysis is an Abstract class. get_output_file_parameter_names must be redefined.")

    def has_all_results(self, step_ids=None):
        # here we use the hard-coded outputs list in
        # IntraAnalysisParameterNames since we cannot determine automatically
        # from a pipeline if all outputs are expected or not (many are
        # optional, but still useful in our context)
        self.propagate_parameters()
        pipeline = self.pipeline
        for parameter in self.get_output_file_parameter_names():
            if self.is_parameter_in_steps(parameter, step_ids=step_ids):
                value = getattr(pipeline, parameter)
                if not isinstance(value, six.string_types) \
                        or not os.path.exists(value):
                    return False
        return True


class ImportationError(Exception):
    pass

