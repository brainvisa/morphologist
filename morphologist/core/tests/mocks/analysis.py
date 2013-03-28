import os
import glob

from morphologist.core.steps import Step
from morphologist.core.analysis import Analysis, Parameters, ParameterTemplate
from morphologist.core.subject import Subject


class MockParameterTemplate(ParameterTemplate):
    input_file_param_names = ['input_1', 'input_2', 'input_5']
    input_other_param_names = ['input_3', 'input_4', 'input_6']
    output_file_param_names = ['output_1', 'output_2', 'output_3', 'output_4',
                               'output_5', 'output_6']
    
    @classmethod
    def get_empty_inputs(cls):
        return Parameters(file_param_names=cls.input_file_param_names,
                          other_param_names=cls.input_other_param_names)

    @classmethod
    def get_empty_outputs(cls):
        return Parameters(file_param_names=cls.output_file_param_names)
    
    @classmethod
    def get_subject_filename(cls, subject, outputdir):
        return cls._generate_in_file_path(subject.name, "in1", outputdir)
    
    @classmethod
    def get_inputs(cls, subject, outputdir):
        inputs = cls.get_empty_inputs()
        inputs.input_1 = cls.get_subject_filename(subject, outputdir)
        inputs.input_2 = cls._generate_in_file_path(subject.name, "in2", outputdir)
        inputs.input_3 = 1.2 
        inputs.input_4 = 2.3 
        inputs.input_5 = cls._generate_in_file_path(subject.name, "in5", outputdir)
        inputs.input_6 = 4.6
        return inputs 

    @classmethod
    def _generate_in_file_path(cls, prefix, filename, outputdir):
        file_path = cls._generate_file_path(prefix + '_' + filename, outputdir)
        f = open(file_path, "w")
        f.close()
        return file_path

    @classmethod
    def _generate_out_file_path(cls, prefix, filename, outputdir):
        file_path = cls._generate_file_path(prefix + '_' + filename, outputdir)
        if os.path.isfile(file_path):
            os.remove(file_path)
        return file_path

    @classmethod
    def _generate_file_path(cls, filename, outputdir):
        return os.path.join(outputdir, filename)

    @classmethod
    def get_outputs(cls, subject, outputdir):
        outputs = cls.get_empty_outputs()
        outputs.output_1 = cls._generate_out_file_path(subject.name, "out1", outputdir)
        outputs.output_2 = cls._generate_out_file_path(subject.name, "out2", outputdir)
        outputs.output_3 = cls._generate_out_file_path(subject.name, "out3", outputdir)
        outputs.output_4 = cls._generate_out_file_path(subject.name, "out4", outputdir)
        outputs.output_5 = cls._generate_out_file_path(subject.name, "out5", outputdir)
        outputs.output_6 = cls._generate_out_file_path(subject.name, "out6", outputdir)
        return outputs
    
    @classmethod
    def create_outputdirs(cls, subject, outputdir):
        pass
    
    @classmethod
    def remove_dirs(cls, subject, outputdir):
        pass
    
    @classmethod
    def get_subjects(cls, directory):
        subjects = []
        print os.listdir(directory)
        glob_pattern = os.path.join(directory, "*_in1")
        for filename in glob.iglob(glob_pattern):
            subjectname = os.path.basename(filename).replace("_in1", "")
            subject = Subject(subjectname, Subject.DEFAULT_GROUP, filename)
            subjects.append(subject)
        return subjects
        
        
class MockAnalysis(Analysis):
    DUMMY_TEMPLATE = "dummy"
    PARAMETER_TEMPLATES = [DUMMY_TEMPLATE]
    param_template_map = {DUMMY_TEMPLATE : MockParameterTemplate}

    def __init__(self, parameter_template=None):
        super(MockAnalysis, self).__init__(parameter_template) 
        self.inputs = MockParameterTemplate.get_empty_inputs()
        self.outputs = MockParameterTemplate.get_empty_outputs()

    def _init_steps(self):
        step1 = MockStep('step1')
        step2 = MockStep('step2')
        step3 = MockStep('step3')
        self._steps = [step1, step2, step3] 
    
    @classmethod
    def get_default_parameter_template_name(cls):
        return cls.DUMMY_TEMPLATE
         
    @classmethod
    def import_data(cls, parameter_template, subject, outputdir):
        return parameter_template.get_subject_filename(subject, outputdir)
        
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
