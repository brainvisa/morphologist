import os
import threading

from morphologist.steps import MockStep

class Analysis(object):
     
    def __init__(self, step_flow):
        self._step_flow = step_flow
        self.input_args = self._step_flow.input_args
        self.output_args = self._step_flow.output_args
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
        if not self._execution_thread.is_alive():
            self._execution_thread.setDaemon(True)
            self._execution_thread.start()

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
        for arg_name in self._step_flow.output_args.list_file_argument_names():
            out_file_path = self._step_flow.output_args.get_value(arg_name)
            if os.path.isfile(out_file_path):
                os.remove(out_file_path)


    def wait(self):
        self._execution_thread.join()

    def is_running(self):
        return self._execution_thread.is_alive() 


class Arguments(object):
    
    def __init__(self, argument_names):
        self._argument_names = argument_names
        for name in argument_names:
            setattr(self, name, None)

    def list_file_argument_names(self):
        return self._argument_names

    def get_value(self, name):
        if not name in self._argument_names:
            raise UnknownArgumentName(name)
        return getattr(self, name)


class UnknownArgumentName(Exception):
    pass


class OutputArguments(Arguments):
    pass

class InputArguments(Arguments):
    pass


class StepFlow(object):

    def __init__(self):
        self._steps = []
      
        self.input_args = InputArgs(argument_names=[])
        self.output_args = OutputArgs(argument_names=[])

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

        self.input_args = InputArguments(argument_names=['input_1',
                                                         'input_2',
                                                         'input_3',
                                                         'input_4',
                                                         'input_5',
                                                         'input_6'])
        self.output_args = OutputArguments(argument_names=['output_1',
                                                           'output_2',
                                                           'output_3',
                                                           'output_4',
                                                           'output_5',
                                                           'output_6'])
 
    def propagate_parameters(self):

        self._steps[0].input_1 = self.input_args.input_1
        self._steps[0].input_2 = self.input_args.input_2
        self._steps[0].input_3 = self.input_args.input_3
        self._steps[0].output_1 = self.output_args.output_1
        self._steps[0].output_2 = self.output_args.output_2

        self._steps[1].input_1 = self._steps[0].output_1
        self._steps[1].input_2 = self._steps[0].output_2
        self._steps[1].input_3 = self.input_args.input_4
        self._steps[1].output_1 = self.output_args.output_3
        self._steps[1].output_2 = self.output_args.output_4

        self._steps[2].input_1 = self.input_args.input_5
        self._steps[2].input_2 = self.input_args.input_6
        self._steps[2].input_3 = self._steps[1].output_1
        self._steps[2].output_1 = self.output_args.output_5
        self._steps[2].output_2 = self.output_args.output_6
    
 
    
