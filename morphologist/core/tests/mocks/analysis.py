import os
import glob

from morphologist.core.analysis import SharedPipelineAnalysis
from morphologist.core.subject import Subject
from capsul.api import get_process_instance

# the following 4 lines are a hack to add /tmp to the FOM search path
# before it is used by StudyConfig
from soma.application import Application
soma_app = Application('capsul', plugin_modules=['soma.fom'])
soma_app.initialize()
soma_app.fom_manager.paths.append('/tmp')

fom_content = '''{
    "fom_name": "mock_fom",

    "formats": {
        "NIFTI": "nii",
        "NIFTI gz": "nii.gz"
    },
    "format_lists": {
        "images": ["NIFTI gz", "NIFTI"]
    },

    "shared_patterns": {
      "subject": "<group>-<subject>"
    },

    "processes": {
        "MyPipeline": {
            "input_image":
                [["input:{subject}_input", "images"]],
            "output_image":
                [["output:{subject}_output", "images"]],
        },
        "MyPipeline.node1": {
            "output_image": [["output:{subject}_node1_output", "images"]]
        },
        "MyPipeline.constant": {
            "output_image": [["output:{subject}_constant_output", "images"]]
        }
    }

}
'''
open('/tmp/mock_fom.json', 'w').write(fom_content)


class MockAnalysis(SharedPipelineAnalysis):

    def __init__(self, study):
        study.input_fom = 'mock_fom'
        study.output_fom = 'mock_fom'
        super(MockAnalysis, self).__init__(study)


    def _init_steps(self):
        self._steps = []

    def build_pipeline(self):
        pipeline = get_process_instance(
            'capsul.pipeline.test.test_pipeline.MyPipeline', self.study)
        pipeline.add_pipeline_step('step1', ['constant'])
        pipeline.add_pipeline_step('step2', ['node1'])
        pipeline.add_pipeline_step('step3', ['node2'])
        return pipeline

    def get_attributes(self, subject):
        attributes_dict = {
            'group': subject.groupname,
            'subject': subject.name,
        }
        return attributes_dict

    def set_parameters(self, subject):
        self.subject = subject
        super(MockAnalysis, self).set_parameters(subject)

    def import_data(self, subject):
        self.propagate_parameters()
        filename = self.pipeline.input_image
        dirname = os.path.dirname(filename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        open(filename, 'w').write('blah.\n')
        return filename

    def get_output_file_parameter_names(self):
        return ['output_image']


class MockFailedAnalysis(MockAnalysis):

    def build_pipeline(self):
        def failing_commandline():
            return ["I fail, this is what I am supposed to do."]

        pipeline = super(MockFailedAnalysis, self).build_pipeline()
        failing_process = pipeline.nodes['node1'].process
        failing_process.get_commandline = failing_commandline
        return pipeline


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
