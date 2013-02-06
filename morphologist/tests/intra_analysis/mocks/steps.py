import os

from morphologist.intra_analysis_steps import SpatialNormalization, \
        BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
        GreyWhite, Grey, GreySurface, WhiteSurface, Sulci, SulciLabelling
from morphologist.intra_analysis import IntraAnalysis


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


class MockSpatialNormalization(SpatialNormalization):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_commissure_coordinates,
                       ref_talairach_transformation):
        super(MockSpatialNormalization, self).__init__()
        self.inputs.commissure_coordinates = ref_commissure_coordinates
        self.inputs.talairach_transformation = ref_talairach_transformation


class MockBiasCorrection(BiasCorrection):
    __metaclass__ = MetaAutomockStep

    def __init__(self, ref_hfiltered, ref_white_ridges,
            ref_edges, ref_corrected_mri, ref_variance):
        super(MockBiasCorrection, self).__init__()
        self.inputs.hfiltered = ref_hfiltered
        self.inputs.white_ridges = ref_white_ridges
        self.inputs.edges = ref_edges
        self.inputs.corrected_mri = ref_corrected_mri
        self.inputs.variance = ref_variance


class MockHistogramAnalysis(HistogramAnalysis):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_histo_analysis, ref_histogram):
        super(MockHistogramAnalysis, self).__init__()
        self.inputs.histo_analysis = ref_histo_analysis
        self.inputs.histogram = ref_histogram


class MockBrainSegmentation(BrainSegmentation):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_brain_mask, ref_refined_white_ridges):
        super(MockBrainSegmentation, self).__init__()
        self.inputs.brain_mask = ref_brain_mask
        self.inputs.white_ridges = ref_refined_white_ridges
 

class MockSplitBrain(SplitBrain):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_split_mask):
        super(MockSplitBrain, self).__init__()
        self.inputs.split_mask = ref_split_mask
 

class MockGreyWhite(GreyWhite):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_grey_white):
        super(MockGreyWhite, self).__init__()
        self.inputs.grey_white = ref_grey_white
 

class MockGrey(Grey):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_grey):
        super(MockGrey, self).__init__()
        self.inputs.grey = ref_grey
        
    
class MockWhiteSurface(WhiteSurface):
    __metaclass__ = MetaAutomockStep
    
    def __init__(self, ref_white_surface):
        super(MockWhiteSurface, self).__init__()
        self.inputs.white_surface = ref_white_surface
        

class MockGreySurface(GreySurface):
    __metaclass__ = MetaAutomockStep
  
    def __init__(self, ref_grey_surface):
        super(MockGreySurface, self).__init__()
        self.inputs.grey_surface = ref_grey_surface


class MockSulci(Sulci):
    __metaclass__ = MetaAutomockStep
  
    def __init__(self, ref_sulci, ref_sulci_data):
        super(MockSulci, self).__init__()
        self.inputs.sulci = ref_sulci
        self.inputs.sulci_data = ref_sulci_data


class MockSulciLabelling(SulciLabelling):
    __metaclass__ = MetaAutomockStep

    def __init__(self, ref_labeled_sulci, ref_labeled_sulci_data):
        super(MockSulciLabelling, self).__init__()
        self.inputs.labeled_sulci = ref_labeled_sulci
        self.inputs.labeled_sulci_data = ref_labeled_sulci_data


def main():
    import time, sys, shutil
 
    def _mock_step(args, idle_time):
        time.sleep(idle_time)
        while len(args) > 1:
            target = args.pop()
            source = args.pop()
            print "\ncopy " + repr(source) + " to " + repr(target)
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
