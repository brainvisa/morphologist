from morphologist.steps import Step
from morphologist.steps import BiasCorrection, HistogramAnalysis, BrainSegmentation, SplitBrain


class MockStep(Step):

    def __init__(self):
        super(MockStep, self).__init__()

        self.input_1 = None
        self.input_2 = None
        self.input_3 = None

        #outputs
        self.output_1 = None
        self.output_2 = None

    def get_command(self):
        message = "MockStep "
        message += "inputs: %s %s %s outputs: %s %s" %(self.input_1, 
                                                       self.input_2, 
                                                       self.input_3, 
                                                       self.output_1, 
                                                       self.output_2)
        command = ["echo", "'" + message + "' ;", "sleep", "1"]
        out_file_1 = open( self.output_1, "w")
        out_file_1.close()
        out_file_2 = open(self.output_2, "w")
        out_file_2.close()
        return command

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
                   'sleep', '2']    
        return command

class MockHistogramAnalysis(HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.histo_analysis, self.histo_analysis, ';',
                   'sleep', '2']    
        return command


class MockBrainSegmentation(BrainSegmentation):
    
    def __init__(self, mock_out_files):
        super(MockBrainSegmentation, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.brain_mask, self.brain_mask, ';',
                   'cp', self.out_files.white_ridges, self.white_ridges, ';',
                   'sleep', '2']    
        return command


class MockSplitBrain(SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.split_mask, self.split_mask, ';',
                   'sleep', '2']    
        return command


