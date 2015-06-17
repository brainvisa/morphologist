import copy
import os
import shutil
import traits.api as traits

from morphologist.core.utils import OrderedDict
from capsul.pipeline import pipeline_tools

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
        if step_ids:
            for step_id in step_ids:
                step = self.step_from_id(step_id)
                if step:
                    step.outputs.clear_files()
        else:
            self.outputs.clear_files()

    def list_input_parameters_with_existing_files(self):
        pipeline = self.pipeline.process
        subject = self.subject
        if subject is None:
            return False
        self.create_fom_completion(subject)
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
        self.create_fom_completion(subject)
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


class ParameterTemplate(object):
    name = None

    def __init__(self, base_directory, study):
        self._base_directory = base_directory
        self.study = study

    @classmethod
    def get_empty_inputs(cls):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    @classmethod
    def get_empty_outputs(cls):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    def get_inputs(self, subject):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    def get_outputs(self, subject):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    def create_outputdirs(self, subject):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    def remove_dirs(self, subject):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    def get_subjects(self, exact_match=False):
        raise NotImplementedError("ParameterTemplate is an abstract class")


class UnknownParameterTemplate(Exception):
    pass


class MissingParameterValueError(Exception):
    pass


class ImportationError(Exception):
    pass


class Parameters(object):

    def __init__(self, file_param_names, other_param_names=None):
        self._file_param_names = file_param_names
        self._parameter_names = copy.copy(self._file_param_names)
        if other_param_names != None:
            self._parameter_names.extend(other_param_names)
        for name in self._parameter_names:
            setattr(self, name, None)

    # Always use set_value, get_value or [] operator in morphologist code.
    # Access to the parameters using directy member is reserved to external use.
    def __getitem__(self, key):
        return self.get_value(key)

    def __setitem__(self, key, value):
        self.set_value(key, value)

    def get_value(self, name):
        if not name in self._parameter_names:
            raise UnknownParameterName(name)
        return getattr(self, name)

    def set_value(self, name, value):
        if not name in self._parameter_names:
            raise UnknownParameterName(name)
        setattr(self, name, value)

    def some_file_exists(self):
        for name in self._file_param_names:
            file_name = getattr(self, name)
            if os.path.isfile(file_name) or os.path.isdir(file_name):
                return True
        return False

    def all_file_exists(self):
        for name in self._file_param_names:
            file_name = getattr(self, name)
            if not os.path.isfile(file_name) and not os.path.isdir(file_name):
                return False
        return True

    def list_parameters_with_existing_files(self):
        existing_files = {}
        for name in self._file_param_names:
            file_name = getattr(self, name)
            if not file_name:
                print '*** no file *** for:', name, type(file_name)
            if os.path.isfile(file_name) or os.path.isdir(file_name):
                existing_files[name] = file_name
        return existing_files

    def list_file_parameter_names(self):
        return self._file_param_names

    def clear_files(self):
        for param_name in self.list_file_parameter_names():
            filename = self.get_value(param_name)
            self._clear_file(filename)

    @classmethod
    def _clear_file(cls, filename):
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename):
            shutil.rmtree(filename)

    @classmethod
    def unserialize(cls, serialized, relative_directory=None):
        file_param_names = serialized['file_param_names']
        parameter_names = serialized['parameter_names'] 
        other_param_names = []
        for param_name in parameter_names:
            if param_name not in file_param_names:
                other_param_names.append(param_name)    
        parameters = cls(file_param_names, other_param_names)
        for param_name in parameter_names:
            value = serialized['parameter_values'][param_name]
            if relative_directory and param_name in file_param_names:
                value = os.path.join(relative_directory, value)
            parameters.set_value(param_name, value)
        return parameters

    def serialize(self, relative_directory=None):
        serialized = {}
        serialized['file_param_names'] = self._file_param_names
        serialized['parameter_names'] = self._parameter_names
        serialized['parameter_values'] = {}
        for param_name in self._parameter_names:
            value = self.get_value(param_name)
            if relative_directory and param_name in self._file_param_names:
                value = os.path.relpath(value, relative_directory)
            serialized['parameter_values'][param_name] = value
        return serialized


class UnknownParameterName(Exception):
    pass
