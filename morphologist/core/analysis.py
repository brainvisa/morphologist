import copy
import os
import shutil

from morphologist.core.utils import OrderedDict


class Analysis(object):
    PARAMETER_TEMPLATES = []
    param_template_map = {}

    def __init__(self):
        self._init_steps()
        self._init_named_steps()
        self.inputs = Parameters(file_param_names=[])
        self.outputs = Parameters(file_param_names=[])

    def _init_steps(self):
        raise NotImplementedError("Analysis is an Abstract class. propagate_parameter must be redifined.") 

    def _init_named_steps(self):
        self._named_steps = OrderedDict()
        for i, step in enumerate(self._steps):
            step_id = "%d_%s" % (i, step.name)
            self._named_steps[step_id] = step

    def step_from_name(self, name):
        return self._named_steps[name]

    def remaining_commands_to_run(self):
        self.propagate_parameters()
        for step_id, step in self._named_steps.items():
            # skip finished steps
            if step.has_all_results():
                continue
            command = step.get_command()
            yield command, step_id

    @classmethod
    def import_data(cls, parameter_template, subject, outputdir):
        return subject.filename

    def set_parameters(self, parameter_template, subject, outputdir):
        if parameter_template not in self.PARAMETER_TEMPLATES:
            raise UnknownParameterTemplate(parameter_template)

        param_template_instance = self.param_template_map[parameter_template]
        self.inputs = param_template_instance.get_inputs(subject)
        self.outputs = param_template_instance.get_outputs(subject, outputdir)

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

    def clear_results(self, stepnames=None):
        if stepnames:
            for stepname in stepnames:
                step = self.step_from_name(stepname)
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
    def get_inputs(cls, subject):
        raise NotImplementedError("ParameterTemplate is an abstract class")

    @classmethod
    def get_outputs(cls, subject, outputdir):
        raise NotImplementedError("ParameterTemplate is an abstract class")
    
    @classmethod
    def create_outputdirs(cls, subject, outputdir):
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
