import copy
import os
import shutil
import traits.api as traits

from morphologist.core.utils import OrderedDict
from capsul.pipeline import pipeline_tools
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


class Analysis(object):
    # XXX the metaclass automatically registers the Analysis class in the
    # AnalysisFactory and intializes the param_template_map
    __metaclass__ = AnalysisMetaClass

    def __init__(self, study):
        self._init_steps()
        self._init_step_ids()
        self.study = study
        self.pipeline = None  # should be a ProcessWithFom
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

    def has_some_results(self):
        raise NotImplementedError("Analysis is an Abstract class. has_some_results must be redefined.")

    def has_all_results(self):
        raise NotImplementedError("Analysis is an Abstract class. has_all_results must be redefined.")

    def clear_results(self, step_ids=None):
        raise NotImplementedError("Analysis is an Abstract class. clear_results must be redefined.")

    def list_input_parameters_with_existing_files(self):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in pipeline.user_traits().iteritems()
                       if not trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, basestring) and os.path.exists(value):
                params[param_name] = value
        return params

    def list_output_parameters_with_existing_files(self):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.propagate_parameters()
        param_names = [param_name
                       for param_name, trait
                          in pipeline.user_traits().iteritems()
                       if trait.output
                          and (isinstance(trait.trait_type, traits.File)
                               or isinstance(trait.trait_type,
                                             traits.Directory)
                               or isinstance(trait.trait_type, traits.Any))]
        params = {}
        for param_name in param_names:
            value = getattr(pipeline, param_name)
            if isinstance(value, basestring) and os.path.exists(value):
                params[param_name] = value
        return params

        #existing =  pipeline_tools.nodes_with_existing_outputs(
            #self.pipeline.process)
        #params = []
        #for node_name, values in  existing.iteritems():
            #parmams.update(dict(values))
        #return params

    def convert_from_formats(self, old_volumes_format, old_meshes_format):
        def _convert_data(old_name, new_name):
            print 'converting:', old_name, 'to:', new_name
            data = aims.read(old_name)
            aims.write(data, new_name)
        def _remove_data(name):
            # TODO: use aims/somaio IO system for formats extensions
            exts = [['.nii'], ['.nii.gz'], ['.img', '.hdr'], ['.ima', '.dim'],
                    ['.dcm'], ['.mnc'],
                    ['.mesh'], ['.gii'], ['.ply']]
            for fexts in exts:
                for ext in fexts:
                    if name.endswith(ext):
                        basename =  name[:-len(ext)]
                        real_exts = fexts + [fexts[0] + '.minf']
                        for cext in real_exts:
                            filename = basename + cext
                            if os.path.isdir(filename):
                                print 'rmtree', filename
                                shutil.rmtree(filename)
                            elif os.path.exists(filename):
                                print 'rm', filename
                                os.unlink(filename)
        print 'convert analysis', self.subject, 'from formats:', old_volumes_format, old_meshes_format, 'to:', self.study.volumes_format, self.study.meshes_format
        if old_volumes_format == self.study.volumes_format \
                and old_meshes_format == self.study.meshes_format:
            print '    nothing to do.'
            return
        old_params = self.parameters
        # force re-running FOM
        self.set_parameters(self.subject)
        todo = [(old_params, self.parameters)]
        while todo:
            old_dict, new_dict = todo.pop(0)
            old_state = old_dict.get('state')
            new_state = new_dict.get('state', {})
            for key, value in old_state.iteritems():
                if isinstance(value, basestring) and os.path.exists(value):
                    new_value = new_state.get(key)
                    if new_value not in ('', None, traits.Undefined) \
                            and new_value != value:
                        _convert_data(value, new_value)
                    if new_value != value:
                        _remove_data(value)
            old_nodes = old_dict.get('nodes')
            new_nodes = new_dict.get('nodes', {})
            if old_nodes:
                todo += [(node, new_nodes.get(key, {}))
                         for key, node in old_nodes.iteritems()]



class ImportationError(Exception):
    pass

