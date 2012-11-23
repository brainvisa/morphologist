import os

class Step(object):
    ''' Abstract class '''

    def __init__(self):
        pass

    def run(self):
        separator = " "
        to_execute = separator.join(self.get_command())
        print "run the command: \n" + to_execute + "\n"
        return os.system(to_execute)

    def get_command(self):
        raise Exception("Step is an abstract class.")


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



class SpatialNormalization(Step):

    def __init__(self):
        super(SpatialNormalization, self).__init__()
        
        self.mri = None
        
        #outputs
        self.commissure_coordinates = None
        self.talairach_transform = None

    def get_command(self):
        # TODO 
        command = ['echo', "TO DO : Spatial Normalization !!!"]
        return command
 

class BiasCorrection(Step):

    def __init__(self):
        super(BiasCorrection, self).__init__()

        self.mri = None
        self.commissure_coordinates = None 
        self.fix_random_seed = False
        #outputs
        self.hfiltered = None
        self.white_ridges = None
        self.edges = None
        self.variance = None
        self.mri_corrected = None

    
    def get_command(self):
        command = ['VipT1BiasCorrection', 
                   '-i', self.mri, 
                   '-o', self.mri_corrected, 
                   '-Wwrite', 'yes',
                   '-wridge', self.white_ridges, 
                   '-eWrite', 'yes',
                   '-ename', self.edges, 
                   '-vWrite', 'yes',
                   '-vname', self.variance, 
                   '-hWrite', 'yes',
                   '-hname', self.hfiltered, 
                   '-Points', self.commissure_coordinates,
                   '-Kregul', "20.0",
                   '-sampling', "16.0",
                   '-Kcrest', "20.0",
                   '-Grid', "2",
                   '-ZregulTuning', "0.5",
                   '-vp', "75",
                   '-e', "3",
                   '-Last', "auto"]
        if self.fix_random_seed:
            command.extend(['-srand', '10'])                

        # TODO referentials
        return command

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

     
class HistogramAnalysis(Step):

    def __init__(self):
        super(HistogramAnalysis, self).__init__()

        self.mri_corrected = None
        self.hfiltered = None
        self.white_ridges = None
        self.fix_random_seed = False
        # output
        self.histo_analysis = None 

   
    def get_command(self):
        command = ['VipHistoAnalysis', 
                   '-i', self.mri_corrected, 
                   '-o', self.histo_analysis, 
                   '-Save', 'y',
                   '-Mask', self.hfiltered,
                   '-Ridge', self.white_ridges,
                   '-mode', 'i']
        if self.fix_random_seed:
            command.extend(['-srand', '10'])  
        return command


class MockHistogramAnalysis(HistogramAnalysis):
    
    def __init__(self, mock_out_files):
        super(MockHistogramAnalysis, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.histo_analysis, self.histo_analysis, ';',
                   'sleep', '2']    
        return command



class BrainSegmentation(Step):

    def __init__(self):
        super(BrainSegmentation, self).__init__()

        self.mri_corrected = None
        self.commissure_coordinates = None
        self.edges = None
        self.variance = None
        self.histo_analysis = None
        self.erosion_size = 1.8
        self.fix_random_seed = False
        # output
        self.brain_mask = None
        self.white_ridges = None #input/output
         

    def get_command(self):
        command = ['VipGetBrain',
                   '-berosion', str(self.erosion_size),
                   '-i', self.mri_corrected,
                   '-analyse', 'r', 
                   '-hname',  self.histo_analysis,
                   '-bname', self.brain_mask,
                   '-First', "0",
                   '-Last', "0", 
                   '-layer', "0",
                   '-Points', self.commissure_coordinates,
                   '-m', "V",
                   '-Variancename', self.variance,
                   '-Edgesname', self.edges,
                   '-Ridge', self.white_ridges,
                   ]
        if self.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials
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


class SplitBrain(Step):

    def __init__(self):
        super(SplitBrain, self).__init__()

        self.mri_corrected = None
        self.brain_mask = None
        self.white_ridges = None
        self.histo_analysis = None
        self.commissure_coordinates = None
        self.bary_factor = 0.6
        self.fix_random_seed = False
        # output
        self.split_mask = None
   
    def get_command(self):
        command = ['VipSplitBrain',
                   '-input',  self.mri_corrected,
                   '-brain', self.brain_mask,
                   '-analyse', 'r', 
                   '-hname', self.histo_analysis,
                   '-output', self.split_mask,
                   '-mode', "'Watershed (2011)'",
                   '-erosion', "2.0",
                   '-ccsize', "500",
                   '-Ridge', self.white_ridges,
                   '-Bary', str(self.bary_factor),
                   '-walgo','b',
                   '-Points', self.commissure_coordinates]
        if self.fix_random_seed:
            command.extend(['-srand', '10'])  

        # TODO:
        # useful option ?? 
        # "-template", "share/brainvisa-share-4.4/hemitemplate/closedvoronoi.ima"
        # "-TemplateUse", "y" 

        # TODO referencials

        return command
    

class MockSplitBrain(SplitBrain):
    
    def __init__(self, mock_out_files):
        super(MockSplitBrain, self).__init__()
        self.out_files = mock_out_files
 
    def get_command(self):
        command = ['cp', self.out_files.split_mask, self.split_mask, ';',
                   'sleep', '2']    
        return command


