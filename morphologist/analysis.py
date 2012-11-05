import copy
import os
import threading

from morphologist.steps import MockStep

class Analysis(object):
     
    def __init__(self, step_flow):
        self._step_flow = step_flow
        self.input_params = self._step_flow.input_params
        self.output_params = self._step_flow.output_params
        self._execution_thread = threading.Thread(name = "analysis run",
                                                  target = Analysis._sync_run,
                                                  args =([self]))
        self._lock = threading.RLock()
        self._interruption = False

    def _sync_run(self):
        command_list = self._step_flow.get_command_list()
        separator = " " 
        for command in command_list:
            with self._lock:
                if self._interruption:
                    self._interruption = False
                    break
            command_to_run = separator.join(command)
            print "\nrun: " + repr(command_to_run)
            os.system(command_to_run)


    def run(self):
        self._check_parameter_values_filled()
        self._check_input_files_exist()
        self._check_output_files_dont_exist()
        if not self._execution_thread.is_alive():
            self._execution_thread.setDaemon(True)
            self._execution_thread.start()


    def _check_parameter_values_filled(self):
        missing_parameters = []
        missing_parameters.extend(self._step_flow.input_params.list_missing_parameter_values())  
        missing_parameters.extend(self._step_flow.output_params.list_missing_parameter_values())
        if missing_parameters:
            separator = " ,"
            message = separator.join(missing_parameters)
            raise MissingParameterValueError(message)


    def _check_input_files_exist(self):
        missing_files = self._step_flow.input_params.list_missing_files()
        if missing_files:
            separator = " ,"
            message = separator.join(missing_files)
            raise MissingInputFileError(message)


    def _check_output_files_dont_exist(self):
        existing_files = self._step_flow.output_params.list_existing_files()
        if existing_files:
            separator = " ,"
            message = separator.join(existing_files)
            raise OutputFileExistError(message) 


    def is_running(self):
        return self._execution_thread.is_alive() 


    def wait(self):
        self._execution_thread.join()


    def stop(self):
        with self._lock:
            self._interruption = True
        self._execution_thread.join()
        with self._lock:
            if self._interruption:
                # the thread ended without being interrupted
                self._interruption = False
            else:
                self.clear_output_files()


    def clear_output_files(self):
        for param_name in self._step_flow.output_params.list_file_parameter_names():
            out_file_path = self._step_flow.output_params.get_value(param_name)
            if os.path.isfile(out_file_path):
                os.remove(out_file_path)


class MissingParameterValueError(Exception):
    pass

class MissingInputFileError(Exception):
    pass

class OutputFileExistError(Exception):
    pass


class Parameters(object):
    
    def __init__(self, file_param_names, other_param_names=None):
        self._file_param_names = file_param_names
        self._parameter_names = copy.copy(self._file_param_names)
        if other_param_names != None:
            self._parameter_names.extend(other_param_names)
        for name in self._parameter_names:
            setattr(self, name, None)

    def list_missing_parameter_values(self):
        missing_values = []
        for name in self._parameter_names:
            if getattr(self, name) == None:
                missing_values.append(name)
        return missing_values

    def list_missing_files(self):
        missing_files = []
        for name in self._file_param_names:
            file_name = getattr(self, name)
            if not os.path.isfile(file_name):
                missing_files.append(file_name)
        return missing_files

    def list_existing_files(self):
        existing_files = [] 
        for name in self._file_param_names:
            file_name = getattr(self, name)
            if os.path.isfile(file_name):
                existing_files.append(file_name)
        return existing_files
        
    def list_file_parameter_names(self):
        return self._file_param_names

    def get_value(self, name):
        if not name in self._parameter_names:
            raise UnknownParameterName(name)
        return getattr(self, name)


class UnknownParameterName(Exception):
    pass


class OutputParameters(Parameters):
    pass

class InputParameters(Parameters):
    pass


class StepFlow(object):

    def __init__(self):
        self._steps = []
      
        self.input_params = InputParameters(parameter_names=[])
        self.output_params = OutputParameters(parameter_names=[])

    def get_command_list(self):
        self.propagate_parameters()
        command_list = []
        for step in self._steps:
             command_list.append(step.get_command())
        return command_list

    def propagate_parameters(self):
        raise Exception("StepFlow is an Abstract class. propagate_parameter must be redifined.") 
      
class MockStepFlow(StepFlow):

    def __init__(self):
        step1 = MockStep()
        step2 = MockStep()
        step3 = MockStep()
        self._steps = [step1, step2, step3] 

        
        self.input_params = InputParameters(file_param_names=['input_1',
                                                              'input_2',
                                                              'input_3',
                                                              'input_4',
                                                              'input_5',
                                                              'input_6'])
        self.output_params = OutputParameters(file_param_names=['output_1',
                                                                'output_2',
                                                                'output_3',
                                                                'output_4',
                                                                'output_5',
                                                                'output_6'])
 
    def propagate_parameters(self):

        self._steps[0].input_1 = self.input_params.input_1
        self._steps[0].input_2 = self.input_params.input_2
        self._steps[0].input_3 = self.input_params.input_3
        self._steps[0].output_1 = self.output_params.output_1
        self._steps[0].output_2 = self.output_params.output_2

        self._steps[1].input_1 = self._steps[0].output_1
        self._steps[1].input_2 = self._steps[0].output_2
        self._steps[1].input_3 = self.input_params.input_4
        self._steps[1].output_1 = self.output_params.output_3
        self._steps[1].output_2 = self.output_params.output_4

        self._steps[2].input_1 = self.input_params.input_5
        self._steps[2].input_2 = self.input_params.input_6
        self._steps[2].input_3 = self._steps[1].output_1
        self._steps[2].output_1 = self.output_params.output_5
        self._steps[2].output_2 = self.output_params.output_6
    
 
    
