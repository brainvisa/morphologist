import os

from morphologist.core.steps import Step
from morphologist.core.analysis import Analysis, Parameters

        
class MockAnalysis(Analysis):
    DUMMY_TEMPLATE = "dummy"
    PARAMETER_TEMPLATES = [DUMMY_TEMPLATE]

    def __init__(self):
        super(MockAnalysis, self).__init__() 
        self.inputs = Parameters(file_param_names=['input_1',
                                                    'input_2',
                                                    'input_5'],
                                 other_param_names=['input_3',
                                                    'input_4',
                                                    'input_6'])
        self.outputs = Parameters(file_param_names=['output_1',
                                                    'output_2',
                                                    'output_3',
                                                    'output_4',
                                                    'output_5',
                                                    'output_6'])

    def _init_steps(self):
        step1 = MockStep('step1')
        step2 = MockStep('step2')
        step3 = MockStep('step3')
        self._steps = [step1, step2, step3] 

    def propagate_parameters(self):
        self._steps[0].inputs.input_1 = self.inputs.input_1
        self._steps[0].inputs.input_2 = self.inputs.input_2
        self._steps[0].inputs.input_3 = self.inputs.input_3
        self._steps[0].outputs.output_1 = self.outputs.output_1
        self._steps[0].outputs.output_2 = self.outputs.output_2

        self._steps[1].inputs.input_1 = self._steps[0].outputs.output_1
        self._steps[1].inputs.input_2 = self._steps[0].outputs.output_2
        self._steps[1].inputs.input_3 = self.inputs.input_4
        self._steps[1].outputs.output_1 = self.outputs.output_3
        self._steps[1].outputs.output_2 = self.outputs.output_4

        self._steps[2].inputs.input_1 = self.inputs.input_5
        self._steps[2].inputs.input_2 = self._steps[1].outputs.output_1
        self._steps[2].inputs.input_3 = self.inputs.input_6
        self._steps[2].outputs.output_1 = self.outputs.output_5
        self._steps[2].outputs.output_2 = self.outputs.output_6
 
    def set_parameters(self, parameter_template, subject, outputdir):
        self.inputs.input_1 = self._generate_in_file_path(subject.name, "in1", outputdir)
        self.inputs.input_2 = self._generate_in_file_path(subject.name, "in2", outputdir)
        self.inputs.input_3 = 1.2 
        self.inputs.input_4 = 2.3 
        self.inputs.input_5 = self._generate_in_file_path(subject.name, "in5", outputdir)
        self.inputs.input_6 = 4.6 

        self.outputs.output_1 = self._generate_out_file_path(subject.name, "out1", outputdir)
        self.outputs.output_2 = self._generate_out_file_path(subject.name, "out2", outputdir)
        self.outputs.output_3 = self._generate_out_file_path(subject.name, "out3", outputdir)
        self.outputs.output_4 = self._generate_out_file_path(subject.name, "out4", outputdir)
        self.outputs.output_5 = self._generate_out_file_path(subject.name, "out5", outputdir)
        self.outputs.output_6 = self._generate_out_file_path(subject.name, "out6", outputdir)

        
    def _generate_in_file_path(self, prefix, filename, outputdir):
        file_path = self._generate_file_path(prefix + '_' + filename, outputdir)
        f = open(file_path, "w")
        f.close()
        return file_path

    def _generate_out_file_path(self, prefix, filename, outputdir):
        file_path = self._generate_file_path(prefix + '_' + filename, outputdir)
        if os.path.isfile(file_path):
            os.remove(file_path)
        return file_path

    def _generate_file_path(self, filename, outputdir):
        return os.path.join(outputdir, filename)


class MockStep(Step):

    def __init__(self, name):
        super(MockStep, self).__init__()
        self.time_to_sleep = 0
        self.name = name

    def _get_authorized_attributes(self):
        return Step._get_authorized_attributes(self) + ['time_to_sleep']

    def _get_inputs(self):
        file_inputs = ['input_1', 'input_2', 'input_3']
        other_inputs = []
        return file_inputs, other_inputs  

    def _get_outputs(self):               
        return ['output_1', 'output_2']

    def get_command(self):
        command = ['python', '-m',
                   'morphologist.core.tests.mocks.analysis',
                    str(self.time_to_sleep),
                    self.outputs.output_1, self.outputs.output_2]
        return command


class MockFailedAnalysis(MockAnalysis):
    
    def _init_steps(self):
        step1 = MockStep('step1')
        step2 = MockFailedStep('failed_step2')
        step3 = MockStep('step3')
        self._steps = [step1, step2, step3] 


class MockFailedStep(MockStep):
                    
    def get_command(self):
        command = super(MockFailedStep, self).get_command()
        command.append("--fail")
        return command
     

def main():
    import sys
    import time
    import optparse
    
    parser = optparse.OptionParser()
    parser.add_option('-f', '--fail', action='store_true',
                      dest="fail", default=False, 
                      help="Execute only this test function.")
    options, args = parser.parse_args(sys.argv)
    
    time_to_sleep = int(args[1])
    args = args[2:]
    
    for filename in args:
        fd = open(filename, "w")
        fd.close()
    time.sleep(time_to_sleep)
    
    if options.fail:
        sys.exit(1)

if __name__ == '__main__' : main()
