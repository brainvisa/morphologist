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


class MockSpatialNormalization(AutomockStep, SpatialNormalization):
    
    def __init__(self, mock_out_files):
        super(MockSpatialNormalization, self).__init__()
        self.out_files = mock_out_files
        self.name = 'normalization'
        self.inputs.commissure_coordinates = self.out_files[IntraAnalysis.COMMISSURE_COORDINATES]
        self.inputs.talairach_transformation = self.out_files[IntraAnalysis.TALAIRACH_TRANSFORMATION]


class MockBiasCorrection(AutomockStep, BiasCorrection):

    def __init__(self, mock_out_files):
        super(MockBiasCorrection, self).__init__()
        self.out_files = mock_out_files
        self.name = 'bias_correction'
        self.inputs.hfiltered = self.out_files[IntraAnalysis.HFILTERED]
        self.inputs.white_ridges = self.out_files[IntraAnalysis.WHITE_RIDGES]
        self.inputs.edges = self.out_files[IntraAnalysis.EDGES]
        self.inputs.corrected_mri = self.out_files[IntraAnalysis.CORRECTED_MRI]
        self.inputs.variance = self.out_files[IntraAnalysis.VARIANCE]
 

class MockHistogramAnalysis(AutomockStep, HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
        self.name = 'histogram_analysis'
        self.inputs.histo_analysis = self.out_files[IntraAnalysis.HISTO_ANALYSIS]
        self.inputs.histogram = self.out_files[IntraAnalysis.HISTOGRAM]


class MockBrainSegmentation(AutomockStep, BrainSegmentation):
    
    def __init__(self, mock_out_files):
        super(MockBrainSegmentation, self).__init__()
        self.out_files = mock_out_files
        self.name = 'brain_segmentation'
        self.inputs.brain_mask = self.out_files[IntraAnalysis.BRAIN_MASK]
        self.inputs.white_ridges = self.out_files[IntraAnalysis.WHITE_RIDGES]
 

class MockSplitBrain(AutomockStep, SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
        self.name = 'split_brain'
        self.inputs.split_mask = self.out_files[IntraAnalysis.SPLIT_MASK]
 

class MockGreyWhite(AutomockStep, GreyWhite):
    
    def __init__(self, ref_grey_white):
        super(MockGreyWhite, self).__init__()
        self.name = 'grey_white'
        self.inputs.grey_white = ref_grey_white
 

class MockGrey(AutomockStep, Grey):
    
    def __init__(self, ref_grey):
        super(MockGrey, self).__init__()
        self.name = 'grey'
        self.inputs.grey = ref_grey
        
    
class MockWhiteSurface(AutomockStep, WhiteSurface):
    
    def __init__(self, ref_white_surface):
        super(MockWhiteSurface, self).__init__()
        self.name = 'white_surface'
        self.inputs.white_surface = ref_white_surface
        

class MockGreySurface(GreySurface):
  
    def __init__(self, ref_grey_surface):
        super(MockGreySurface, self).__init__()
        self.name = 'grey_surface'
        self.inputs.grey_surface = ref_grey_surface

    def get_command(self):
        command = ['python', '-m',
                   'morphologist.tests.intra_analysis.mocks.steps', self.name,
                   self.inputs.grey_surface,
                   self.outputs.grey_surface]
        return command


class MockSulci(Sulci):
  
    def __init__(self, ref_sulci):
        super(MockSulci, self).__init__()
        self.name = 'sulci'
        self.inputs.sulci = ref_sulci

    def get_command(self):
        command = ['python', '-m',
                   'morphologist.tests.intra_analysis.mocks.steps', self.name,
                   self.inputs.sulci,
                   self.outputs.sulci,
                   self.inputs.sulci.replace(".arg", ".data"),
                   self.outputs.sulci.replace(".arg", ".data")]
        return command


class MockSulciLabelling(SulciLabelling):

    def __init__(self, ref_labeled_sulci):
        super(MockSulciLabelling, self).__init__()
        self.name = 'sulci_labelling'
        self.inputs.labeled_sulci = ref_labeled_sulci

    def get_command(self):
        command = ['python', '-m',
                   'morphologist.tests.intra_analysis.mocks.steps', self.name,
                   self.inputs.labeled_sulci,
                   self.outputs.labeled_sulci,
                   self.inputs.labeled_sulci.replace(".arg", ".data"),
                   self.outputs.labeled_sulci.replace(".arg", ".data")]
        return command


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
