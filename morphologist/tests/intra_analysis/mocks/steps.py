from morphologist.intra_analysis_steps import SpatialNormalization, \
        BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain, \
        GreyWhite, Grey, WhiteSurface
from morphologist.intra_analysis import IntraAnalysis


class MockSpatialNormalization(SpatialNormalization):
    
    def __init__(self, mock_out_files):
        super(MockSpatialNormalization, self).__init__()
        self.out_files = mock_out_files
        
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'normalization',
            self.out_files[IntraAnalysis.COMMISSURE_COORDINATES], self.commissure_coordinates,
            self.out_files[IntraAnalysis.TALAIRACH_TRANSFORMATION], self.talairach_transformation]
        return command


class MockBiasCorrection(BiasCorrection):

    def __init__(self, mock_out_files):
        super(MockBiasCorrection, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps', 'bias_correction',
            self.out_files[IntraAnalysis.HFILTERED], self.hfiltered,
            self.out_files[IntraAnalysis.WHITE_RIDGES], self.white_ridges, 
            self.out_files[IntraAnalysis.EDGES], self.edges, 
            self.out_files[IntraAnalysis.CORRECTED_MRI], self.corrected_mri, 
            self.out_files[IntraAnalysis.VARIANCE], self.variance]
        return command


class MockHistogramAnalysis(HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'histogram_analysis',
            self.out_files[IntraAnalysis.HISTO_ANALYSIS], self.histo_analysis,
            self.out_files[IntraAnalysis.HISTOGRAM], self.histogram]
        return command


class MockBrainSegmentation(BrainSegmentation):
    
    def __init__(self, mock_out_files):
        super(MockBrainSegmentation, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'brain_segmentation',
            self.out_files[IntraAnalysis.BRAIN_MASK], self.brain_mask,
            self.out_files[IntraAnalysis.WHITE_RIDGES], self.white_ridges]
        return command


class MockSplitBrain(SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps', 'split_brain',
            self.out_files[IntraAnalysis.SPLIT_MASK], self.split_mask]
        return command


class MockGreyWhite(GreyWhite):
    
    def __init__(self, ref_grey_white):
        super(MockGreyWhite, self).__init__()
        self.ref_grey_white = ref_grey_white
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'grey_white',
            self.ref_grey_white, 
            self.grey_white]
        return command


class MockGrey(Grey):
    
    def __init__(self, ref_grey):
        super(MockGrey, self).__init__()
        self.ref_grey = ref_grey
        
    def get_command(self):
        command = ['python', '-m', 
                   'morphologist.tests.intra_analysis.mocks.steps',
                   'grey',
                   self.ref_grey,
                   self.grey]
        return command

    
class MockWhiteSurface(WhiteSurface):
    
    def __init__(self, ref_white_surface):
        super(MockWhiteSurface, self).__init__()
        self.ref_white_surface = ref_white_surface
        
    def get_command(self):
        command = ['python', '-m', 
                   'morphologist.tests.intra_analysis.mocks.steps',
                   'white_surface',
                   self.ref_white_surface,
                   self.white_surface]
        return command

   
def main():
    import time, sys, shutil
 
    def _mock_step(args, idle_time):
        time.sleep(idle_time)
        while len(args) > 1:
            target_file = args.pop()
            source_file = args.pop()
            print "\ncopy " + repr(source_file) + " to " + repr(target_file)
            shutil.copy(source_file, target_file)
 
    stepname = sys.argv[1]
    args = sys.argv[2:]
    time_to_sleep = 0

    _mock_step(args, time_to_sleep)

if __name__ == '__main__' : main()
