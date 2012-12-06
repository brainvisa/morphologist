from morphologist.intra_analysis_steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain

#TODO MockSpatialNormalization

class MockBiasCorrection(BiasCorrection):

    def __init__(self, mock_out_files):
        super(MockBiasCorrection, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.mocks.intra_analysis_steps', 'bias_correction',
            self.out_files.hfiltered, self.hfiltered,
            self.out_files.white_ridges, self.white_ridges, 
            self.out_files.edges, self.edges, 
            self.out_files.mri_corrected, self.mri_corrected, 
            self.out_files.variance, self.variance]
        return command

class MockHistogramAnalysis(HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.mocks.intra_analysis_steps',
            'histogram_analysis',
            self.out_files.histo_analysis, self.histo_analysis]
        return command


class MockBrainSegmentation(BrainSegmentation):
    
    def __init__(self, mock_out_files):
        super(MockBrainSegmentation, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.mocks.intra_analysis_steps',
            'brain_segmentation',
            self.out_files.brain_mask, self.brain_mask,
            self.out_files.white_ridges, self.white_ridges]
        return command


class MockSplitBrain(SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['python', '-m',
            'morphologist.tests.mocks.intra_analysis_steps', 'split_brain',
            self.out_files.split_mask, self.split_mask]
        return command


def main():
    import time, sys, shutil

    stepname = sys.argv[1]
    args = sys.argv[2:]
    time_to_sleep = 2

    if stepname == 'bias_correction':
        out_files_hfiltered, hfiltered, \
        out_files_white_ridges, white_ridges, \
        out_files_edges, edges, \
        out_files_mri_corrected, mri_corrected, \
        out_files_variance, variance = args
        time.sleep(time_to_sleep)
        shutil.copy(out_files_hfiltered, hfiltered)
        shutil.copy(out_files_white_ridges, white_ridges)
        shutil.copy(out_files_edges, edges)
        shutil.copy(out_files_mri_corrected, mri_corrected)
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
    

if __name__ == '__main__' : main()
