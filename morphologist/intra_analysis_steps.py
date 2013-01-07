from morphologist.steps import Step


class ImageImportation(Step):
    
    def __init__(self):
        super(ImageImportation, self).__init__()
        
        self.input = None
        
        self.output = None
        
    def get_command(self):
        command = ["python", "-m", "corist.image_importation", 
                   self.input, 
                   self.output]
        return command
    
    
class SpatialNormalization(Step):

    def __init__(self):
        super(SpatialNormalization, self).__init__()
        
        self.mri = None
        
        #outputs
        self.commissure_coordinates = None
        self.talairach_transformation = None

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_normalization', 
                   self.mri, 
                   self.commissure_coordinates, 
                   self.talairach_transformation]
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
        self.corrected_mri = None

    
    def get_command(self):
        command = ['VipT1BiasCorrection', 
                   '-i', self.mri, 
                   '-o', self.corrected_mri, 
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

        # TODO referentials ?
        return command

     
class HistogramAnalysis(Step):

    def __init__(self):
        super(HistogramAnalysis, self).__init__()

        self.corrected_mri = None
        self.hfiltered = None
        self.white_ridges = None
        self.fix_random_seed = False
        # output
        self.histo_analysis = None 

   
    def get_command(self):
        command = ['VipHistoAnalysis', 
                   '-i', self.corrected_mri, 
                   '-o', self.histo_analysis, 
                   '-Save', 'y',
                   '-Mask', self.hfiltered,
                   '-Ridge', self.white_ridges,
                   '-mode', 'i']
        if self.fix_random_seed:
            command.extend(['-srand', '10'])  
        return command


class BrainSegmentation(Step):

    def __init__(self):
        super(BrainSegmentation, self).__init__()

        self.corrected_mri = None
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
                   '-i', self.corrected_mri,
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
        # TODO referentials ?
        return command


class SplitBrain(Step):

    def __init__(self):
        super(SplitBrain, self).__init__()

        self.corrected_mri = None
        self.commissure_coordinates = None
        self.brain_mask = None
        self.white_ridges = None
        self.histo_analysis = None
        self.bary_factor = 0.6
        self.fix_random_seed = False
        # output
        self.split_mask = None
   
    def get_command(self):
        command = ['VipSplitBrain',
                   '-input',  self.corrected_mri,
                   '-brain', self.brain_mask,
                   '-analyse', 'r', 
                   '-hname', self.histo_analysis,
                   '-output', self.split_mask,
                   '-mode', 'Watershed (2011)',
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

        # TODO referentials ?

        return command
    

class AbstractGreyWhite(Step):

    def __init__(self):
        super(AbstractGreyWhite, self).__init__()

        self.corrected_mri = None
        self.commissure_coordinates = None
        self.histo_analysis = None
        self.split_mask = None
        self.edges = None
        self.fix_random_seed = False

    def get_command(self):
        raise Exception("AbstractGreyWhite is an abstract class.")

    def _get_base_command(self):
        command  = ['VipGreyWhiteClassif',
                    '-input', self.corrected_mri,
                    '-Points', self.commissure_coordinates,
                    '-hana', self.histo_analysis,
                    '-mask', self.split_mask,
                    '-edges', self.edges,
                    '-writeformat', 't',
                    '-algo', 'N']
        if self.fix_random_seed:
            command.extend(['-srand', '10'])  
        return command


class LeftGreyWhite(AbstractGreyWhite):

    def __init__(self):
        super(LeftGreyWhite, self).__init__()
        #outputs
        self.left_grey_white = None

    def get_command(self):
        command = self._get_base_command()
        command.extend(['-label', '2', '-output', self.left_grey_white])

        # TODO referentials ?
        return command


class RightGreyWhite(AbstractGreyWhite):

    def __init__(self):
        super(RightGreyWhite, self).__init__()
        #outputs
        self.right_grey_white = None

    def get_command(self):
        command = self._get_base_command()
        command.extend(['-label', '1', '-output', self.right_grey_white])

        # TODO referentials ?
        return command

