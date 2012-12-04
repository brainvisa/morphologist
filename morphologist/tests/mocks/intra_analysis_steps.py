from morphologist.intra_analysis_steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain

#TODO MockSpatialNormalization

class MockBiasCorrection(BiasCorrection):

    def __init__(self, mock_out_files):
        super(MockBiasCorrection, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.hfiltered, self.hfiltered, ';',
                   'cp', self.out_files.white_ridges, self.white_ridges, ';', 
                   'cp', self.out_files.edges, self.edges, ';', 
                   'cp', self.out_files.mri_corrected, self.mri_corrected, ';',
                   'cp', self.out_files.variance, self.variance, ';', 
                   'sleep', '10']    
        return command

class MockHistogramAnalysis(HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.histo_analysis, self.histo_analysis, ';',
                   'sleep', '10']    
        return command


class MockBrainSegmentation(BrainSegmentation):
    
    def __init__(self, mock_out_files):
        super(MockBrainSegmentation, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.brain_mask, self.brain_mask, ';',
                   'cp', self.out_files.white_ridges, self.white_ridges, ';',
                   'sleep', '10']    
        return command


class MockSplitBrain(SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.split_mask, self.split_mask, ';',
                   'sleep', '10']    
        return command


