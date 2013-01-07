from morphologist.intra_analysis_steps import BiasCorrection, \
        HistogramAnalysis, BrainSegmentation, SplitBrain, \
        LeftGreyWhite, RightGreyWhite, \
        SpatialNormalization
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
            self.out_files[IntraAnalysis.HISTO_ANALYSIS], self.histo_analysis]
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


class MockLeftGreyWhite(LeftGreyWhite):
    
    def __init__(self, mock_out_files):
        super(MockLeftGreyWhite, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'grey_white',
            self.out_files[IntraAnalysis.LEFT_GREY_WHITE],
            self.left_grey_white]
        return command


class MockRightGreyWhite(RightGreyWhite):
    
    def __init__(self, mock_out_files):
        super(MockRightGreyWhite, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.intra_analysis.mocks.steps',
            'grey_white',
            self.out_files[IntraAnalysis.RIGHT_GREY_WHITE],
            self.right_grey_white]
        return command


def main():
    import time, sys, shutil

    stepname = sys.argv[1]
    args = sys.argv[2:]
    time_to_sleep = 0

    if stepname == 'normalization':
        out_files_commissure_coordinates, commissure_coordinates, \
        out_files_talairach_transformation, talairach_transformation = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_commissure_coordinates, commissure_coordinates)
        shutil.copy(out_files_talairach_transformation, talairach_transformation)
    elif stepname == 'bias_correction':
        out_files_hfiltered, hfiltered, \
        out_files_white_ridges, white_ridges, \
        out_files_edges, edges, \
        out_files_corrected_mri, corrected_mri, \
        out_files_variance, variance = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_hfiltered, hfiltered)
        shutil.copy(out_files_white_ridges, white_ridges)
        shutil.copy(out_files_edges, edges)
        shutil.copy(out_files_corrected_mri, corrected_mri)
        shutil.copy(out_files_variance, variance)
    elif stepname == 'histogram_analysis':
        out_files_histo_analysis, histo_analysis = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_histo_analysis, histo_analysis)
    elif stepname == 'brain_segmentation':
        out_files_brain_mask, brain_mask, \
            out_files_white_ridges, white_ridges = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_brain_mask, brain_mask)
        shutil.copy(out_files_white_ridges, white_ridges)
    elif stepname == 'split_brain':
        out_files_split_mask, split_mask = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_split_mask, split_mask)
    elif stepname == 'grey_white':
        out_files_grey_white, grey_white = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_grey_white, \
                    grey_white)
    

if __name__ == '__main__' : main()
