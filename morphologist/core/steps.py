import os

from morphologist.core.analysis import InputParameters, OutputParameters


class Step(object):
    ''' Abstract class '''

    def __init__(self):
        file_inputs, other_inputs = self._get_inputs()
        file_outputs = self._get_outputs()
        self.inputs = InputParameters(file_inputs, other_inputs)
        self.outputs = OutputParameters(file_outputs)
        self.name = 'unnamed step'

    def run(self):
        # WARNING do not overload: get_command should be used to run the step 
        to_execute = ""
        for arg in self.get_command():
            to_execute += "\"%s\" " % arg
        print "run the command: \n" + to_execute + "\n"
        return os.system(to_execute)

    def has_all_results(self):
        return self.outputs.all_file_exists()

    def get_command(self):
        raise NotImplementedError("Step is an abstract class.")

    def _get_inputs(self):
        raise NotImplementedError("Step is an abstract class.")

    def _get_outputs(self):
        raise NotImplementedError("Step is an abstract class.")

    def __setattr__(self, attr, value):
        msg = "'%s': invalid attribute: use inputs or outputs instead" % attr
        if attr not in self._get_authorized_attributes():
            raise ValueError(msg)
        object.__setattr__(self, attr, value)

    def _get_authorized_attributes(self):
        return ['inputs', 'outputs', 'name']
