
from morphologist.steps import MockStep

class Analysis(object):
     
    def __init__(self):
        self._steps = []
        self._is_running = False

    def propagate_paramters(self):
        raise Exception("Analysis is an abstract class.")

    def get_command_list(self):
        self.propagate_parameters()
        command_list = []
        for step in self._steps:
             command_list.append(step.get_command())
        return command_list

    def run(self):
        self._is_running = True

    def stop(self):
        self._is_running = False

    def is_running(self):
        return self._is_running

      
class MockAnalysis(Analysis):

    def __init__(self):
        step1 = MockStep()
        step2 = MockStep()
        step3 = MockStep()
        self._steps = [step1, step2, step3] 

        self.input_1 = None
        self.input_2 = None
        self.input_3 = None
        self.input_4 = None
        self.input_5 = None
        self.input_6 = None
        
        self.output_1 = None
        self.output_2 = None
        self.output_3 = None
        self.output_4 = None
        self.output_5 = None
        self.output_6 = None
 
    def propagate_parameters(self):

        self._steps[1].input_1 = self.input_1
        self._steps[1].input_2 = self.input_2
        self._steps[1].input_3 = self.input_3
        self._steps[1].output_1 = self.output_1
        self._steps[1].output_2 = self.output_2

        self._steps[2].input_1 = self._steps[1].output_1
        self._steps[2].input_2 = self._steps[1].output_2
        self._steps[2].input_3 = self.input_4
        self._steps[2].output_1 = self.output_3
        self._steps[2].output_2 = self.output_4

        self._steps[3].input_1 = self.input_5
        self._steps[3].input_2 = self.input_6
        self._steps[3].input_3 = self._steps[2].output_1
        self._steps[3].output_1 = self.output_5
        self._steps[3].output_2 = self.output_6
    
 
    #    def __init__(self):
#        pass
#
#    def run(self):
#        pass
#
#    def stop(self):
#        pass
#
#    def is_running(self):
#        pass
#    
     
