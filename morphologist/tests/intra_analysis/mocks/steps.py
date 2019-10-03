from __future__ import print_function

import os

from morphologist.intra_analysis.steps import SpatialNormalization, \
        BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
        GreyWhite, Grey, GreySurface, WhiteSurface, Sulci, SulciLabelling
from morphologist.intra_analysis import constants
import six


# XXX: spurious information, not used by mock steps but however necessary
dummy_side = constants.LEFT


class AutomockStep(object):

    def _get_inputs(self):
        file_inputs = self._get_outputs()
        other_inputs = []
        return file_inputs, other_inputs

    def get_command(self):
        command = ['python', '-m',
                   'morphologist.tests.intra_analysis.mocks.steps',
                   self.name]
        parameters = []
        for parameter in self.outputs.list_file_parameter_names():
            parameters.append(self.inputs[parameter])
            parameters.append(self.outputs[parameter])
        command.extend(parameters)
        return command

    def step_name(self):
        raise NotImplementedError("AutomockStep is an abstract class")


class MetaAutomockStep(type):
    def __new__(cls, name, bases, dict):
        def func(self):
            StandardStep = self.__class__.__bases__[1]
            std_authorized_attr = StandardStep._get_authorized_attributes(self)
            return ['out_files'] + std_authorized_attr
        ExtendedAutomockStep = type(name, (AutomockStep,) + bases, dict)
        ExtendedAutomockStep._get_authorized_attributes = func
        return ExtendedAutomockStep


class MockSpatialNormalization(
    six.with_metaclass(MetaAutomockStep, SpatialNormalization)):

    def __init__(self):
        super(MockSpatialNormalization, self).__init__()


class MockBiasCorrection(six.with_metaclass(MetaAutomockStep, BiasCorrection)):

    def __init__(self):
        super(MockBiasCorrection, self).__init__()


class MockHistogramAnalysis(
    six.with_metaclass(MetaAutomockStep, HistogramAnalysis)):
    
    def __init__(self):
        super(MockHistogramAnalysis, self).__init__()


class MockBrainSegmentation(
    six.with_metaclass(MetaAutomockStep, BrainSegmentation)):

    def __init__(self):
        super(MockBrainSegmentation, self).__init__()


class MockSplitBrain(six.with_metaclass(MetaAutomockStep, SplitBrain)):

    def __init__(self):
        super(MockSplitBrain, self).__init__()


class MockGreyWhite(six.with_metaclass(MetaAutomockStep, GreyWhite)):

    def __init__(self, side):
        super(MockGreyWhite, self).__init__(side)


class MockGrey(six.with_metaclass(MetaAutomockStep, Grey)):

    def __init__(self, side):
        super(MockGrey, self).__init__(side)


class MockWhiteSurface(six.with_metaclass(MetaAutomockStep, WhiteSurface)):

    def __init__(self, side):
        super(MockWhiteSurface, self).__init__(side)


class MockGreySurface(six.with_metaclass(MetaAutomockStep, GreySurface)):

    def __init__(self, side):
        super(MockGreySurface, self).__init__(side)


class MockSulci(six.with_metaclass(MetaAutomockStep, Sulci)):
  
    def __init__(self, side):
        super(MockSulci, self).__init__(side)


class MockSulciLabelling(six.with_metaclass(MetaAutomockStep, SulciLabelling)):

    def __init__(self, side):
        super(MockSulciLabelling, self).__init__(side)


def main():
    import time, sys, shutil
 
    def _mock_step(args, idle_time):
        time.sleep(idle_time)
        while len(args) > 1:
            target = args.pop()
            source = args.pop()
            print("\ncopy " + repr(source) + " to " + repr(target))
            if os.path.isdir(source):
                if os.path.isdir(target):
                    shutil.rmtree(target)
                shutil.copytree(source, target)
            else:

                shutil.copy(source, target)
 
    stepname = sys.argv[1]
    args = sys.argv[2:]
    time_to_sleep = 0

    _mock_step(args, time_to_sleep)

if __name__ == '__main__' : main()
