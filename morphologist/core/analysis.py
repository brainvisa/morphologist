import copy
import os
import shutil

from morphologist.core.utils import OrderedDict


class AnalysisFactory(object):
    _registered_analyses = {}
    
    @classmethod
    def register_analysis(cls, analysis_type, analysis_class):
        cls._registered_analyses[analysis_type] = analysis_class
        
    @classmethod
    def create_analysis(cls, analysis_type, parameter_template):
        analysis_cls = cls.get_analysis_cls(analysis_type) 
        return analysis_cls(parameter_template)
 
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
    # XXX the metaclass automatically register the Analysis class in the AnalysisFactory
    __metaclass__ = AnalysisMetaClass
    PARAMETER_TEMPLATES = []
    param_template_map = {}

    def __init__(self, parameter_template=None):
        self._init_steps()
        self._init_step_ids()
        if parameter_template is None:
            parameter_template = self.create_default_parameter_template()
        self.parameter_template = parameter_template
        self.inputs = Parameters(file_param_names=[])
        self.outputs = Parameters(file_param_names=[])

    def _init_steps(self):
        raise NotImplementedError("Analysis is an Abstract class.") 

    def _init_step_ids(self):
        self._step_ids = OrderedDict()
        for i, step in enumerate(self._steps):
            step_id = "%d_%s" % (i, step.name)
            self._step_ids[step_id] = step

    @classmethod
    def get_default_parameter_template_name(cls):
        raise NotImplementedError("Analysis is an Abstract class.")
    
    @classmethod
    def create_default_parameter_template(cls):
        return cls.create_parameter_template(cls.get_default_parameter_template_name())
       
    @classmethod
    def  create_parameter_template(cls, parameter_template_name):
        if parameter_template_name not in cls.PARAMETER_TEMPLATES:
            raise UnknownParameterTemplate(parameter_template_name)
        param_template = cls.param_template_map[parameter_template_name]()
        return param_template
        
    def step_from_id(self, step_id):
        return self._step_ids[step_id]

    def remaining_commands_to_run(self):
        self.propagate_parameters()
        for step_id, step in self._step_ids.items():
            # skip finished steps
            if step.has_all_results():
                continue
            command = step.get_command()
            yield command, step_id
    
    @classmethod
    def import_data(cls, parameter_template, subject, outputdir):        
        new_subject_filename = parameter_template.get_subject_filename(subject, outputdir)
        parameter_template.create_outputdirs(subject, outputdir)
        shutil.copy(subject.filename, new_subject_filename)
        return new_subject_filename

    def set_parameters(self, subject, outputdir):
        self.inputs = self.parameter_template.get_inputs(subject, outputdir)
        self.outputs = self.parameter_template.get_outputs(subject, outputdir)

    def get_command_list(self):
        self._check_parameter_values_filled()
        self.propagate_parameters()
        command_list = []
        for step in self._steps:
            command_list.append(step.get_command())
        return command_list

    def propagate_parameters(self):
        raise NotImplementedError("Analysis is an Abstract class. propagate_parameter must be redefined.") 
 
    def _check_parameter_values_filled(self):
        missing_parameters = []
        missing_parameters.extend(self.inputs.list_missing_parameter_values())  
        missing_parameters.extend(self.outputs.list_missing_parameter_values())
        if missing_parameters:
            separator = " ,"
            message = separator.join(missing_parameters)
            raise MissingParameterValueError(message)
        
    def has_some_results(self):
        return self.outputs.some_file_exists()
        
    def has_all_results(self):
        return self.outputs.all_file_exists()
            
    def clear_results(self, step_ids=None):
        if step_ids:
            for step_id in step_ids:
                step = self.step_from_id(step_id)
                step.outputs.clear_files()
        else:
            self.outputs.clear_files()
                
                
class ParameterTemplate(object):
    
    @classmethod
    def get_empty_inputs(cls):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    @classmethod
    def get_empty_outputs(cls):
        raise NotImplementedError("ParameterTemplate is an abstract class")
    
    @classmethod
    def get_subject_filename(cls):
        raise NotImplementedError("ParameterTemplate is an abstract class")
        
    @classmethod
    def get_inputs(cls, subject, outputdir):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    @classmethod
    def get_outputs(cls, subject, outputdir):
        raise NotImplementedError("ParameterTemplate is an abstract class")
    
    @classmethod
    def create_outputdirs(cls, subject, outputdir):
        raise NotImplementedError("ParameterTemplate is an abstract class")
    
    @classmethod
    def remove_dirs(cls, subject, outputdir):
        raise NotImplementedError("ParameterTemplate is an abstract class")
    
    @classmethod
    def get_subjects(cls, directory):
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

    def list_missing_parameter_values(self):
        missing_values = []
        for name in self._parameter_names:
            if getattr(self, name) == None:
                missing_values.append(name)
        return missing_values

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
    def unserialize(cls, serialized):
        file_param_names = serialized['file_param_names']
        parameter_names = serialized['parameter_names'] 
        other_param_names = []
        for param_name in parameter_names:
            if param_name not in file_param_names:
                other_param_names.append(param_name)    
        parameters = cls(file_param_names, other_param_names)
        for param_name in parameter_names:
            parameters.set_value(param_name, serialized['parameter_values'][param_name])
        return parameters          

    def serialize(self):
        serialized = {}
        serialized['file_param_names'] = self._file_param_names
        serialized['parameter_names'] = self._parameter_names
        serialized['parameter_values'] = {}
        for param_name in self._parameter_names:
            serialized['parameter_values'][param_name] = self.get_value(param_name) 
        return serialized
        
    
class UnknownParameterName(Exception):
    pass
