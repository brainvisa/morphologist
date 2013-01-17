from morphologist.steps import Step


class ImageImportation(Step):
    
    def __init__(self):
        super(ImageImportation, self).__init__()

    def _get_inputs(self):
        file_inputs = ['input']
        other_inputs = []
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['output']

    def get_command(self):
        command = ["python", "-m", "corist.image_importation", 
                   self.inputs.input, 
                   self.outputs.output]
        return command
    
    
class SpatialNormalization(Step):

    def __init__(self):
        super(SpatialNormalization, self).__init__()

    def _get_inputs(self):
        file_inputs = ['mri']
        other_inputs = []
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['commissure_coordinates', 'talairach_transformation']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_normalization', 
                   self.inputs.mri, 
                   self.outputs.commissure_coordinates, 
                   self.outputs.talairach_transformation]
        return command
    
        
class BiasCorrection(Step):

    def __init__(self):
        super(BiasCorrection, self).__init__()
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['mri', 'commissure_coordinates']
        other_inputs = ['fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['hfiltered', 'white_ridges', 'edges',
                'variance', 'corrected_mri']

    def get_command(self):
        command = ['VipT1BiasCorrection', 
                   '-i', self.inputs.mri, 
                   '-Points', self.inputs.commissure_coordinates,
                   '-o', self.outputs.corrected_mri, 
                   '-Wwrite', 'yes',
                   '-wridge', self.outputs.white_ridges, 
                   '-eWrite', 'yes',
                   '-ename', self.outputs.edges, 
                   '-vWrite', 'yes',
                   '-vname', self.outputs.variance, 
                   '-hWrite', 'yes',
                   '-hname', self.outputs.hfiltered, 
                   '-Kregul', "20.0",
                   '-sampling', "16.0",
                   '-Kcrest', "20.0",
                   '-Grid', "2",
                   '-ZregulTuning', "0.5",
                   '-vp', "75",
                   '-e', "3",
                   '-Last', "auto"]
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])                
        # TODO referentials ?
        return command

     
class HistogramAnalysis(Step):

    def __init__(self):
        super(HistogramAnalysis, self).__init__()
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'hfiltered', 'white_ridges']
        other_inputs = ['fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['histo_analysis', 'histogram']

    def get_command(self):
        command = ['VipHistoAnalysis', 
                   '-i', self.inputs.corrected_mri, 
                   '-Mask', self.inputs.hfiltered,
                   '-Ridge', self.inputs.white_ridges,
                   '-o', self.outputs.histo_analysis, 
                   '-output-his', self.outputs.histogram, 
                   '-Save', 'y',
                   '-mode', 'i']
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        return command


class BrainSegmentation(Step):

    def __init__(self):
        super(BrainSegmentation, self).__init__()
        self.inputs.erosion_size = 1.8
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'edges', 'variance', 'histo_analysis']
        other_inputs = ['erosion_size', 'fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['brain_mask',
                'white_ridges'] #input/output
 
    def get_command(self):
        command = ['VipGetBrain',
                   '-i', self.inputs.corrected_mri,
                   '-Points', self.inputs.commissure_coordinates,
                   '-berosion', str(self.inputs.erosion_size),
                   '-Edgesname', self.inputs.edges,
                   '-Variancename', self.inputs.variance,
                   '-hname',  self.inputs.histo_analysis,
                   '-bname', self.outputs.brain_mask,
                   '-Ridge', self.outputs.white_ridges,
                   '-analyse', 'r', 
                   '-First', "0",
                   '-Last', "0", 
                   '-layer', "0",
                   '-m', "V"]
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials ?
        return command


class SplitBrain(Step):

    def __init__(self):
        super(SplitBrain, self).__init__()
        self.inputs.bary_factor = 0.6
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'brain_mask', 'white_ridges', 'histo_analysis']
        other_inputs = ['bary_factor', 'fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['split_mask']
   
    def get_command(self):
        command = ['VipSplitBrain',
                   '-input',  self.inputs.corrected_mri,
                   '-Points', self.inputs.commissure_coordinates,
                   '-brain', self.inputs.brain_mask,
                   '-Ridge', self.inputs.white_ridges,
                   '-hname', self.inputs.histo_analysis,
                   '-Bary', str(self.inputs.bary_factor),
                   '-output', self.outputs.split_mask,
                   '-analyse', 'r', 
                   '-mode', 'Watershed (2011)',
                   '-erosion', "2.0",
                   '-ccsize', "500",
                   '-walgo','b']
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO:
        # useful option ?? 
        # "-template", "share/brainvisa-share-4.4/hemitemplate/closedvoronoi.ima"
        # "-TemplateUse", "y" 
        # TODO referentials ?
        return command
    

class GreyWhite(Step):

    def __init__(self, left=True):
        super(GreyWhite, self).__init__()
        self.left = left
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'histo_analysis', 'split_mask', 'edges']
        other_inputs = ['fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['grey_white']

    def get_command(self):
        command  = ['VipGreyWhiteClassif',
                    '-input', self.inputs.corrected_mri,
                    '-Points', self.inputs.commissure_coordinates,
                    '-hana', self.inputs.histo_analysis,
                    '-mask', self.inputs.split_mask,
                    '-edges', self.inputs.edges,
                    '-writeformat', 't',
                    '-algo', 'N']
        if self.left:
            label = '2'
        else:
            label = '1'
        command.extend(['-label', label, '-output', self.outputs.grey_white])
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials ?
        return command


class Grey(Step):

    def __init__(self):
        super(Grey, self).__init__()
        self.inputs.fix_random_seed = False

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'histo_analysis', 'grey_white']
        other_inputs = ['fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['grey']

    def get_command(self):
        command = ['VipHomotopic',
                   '-input', self.inputs.corrected_mri,
                   '-classif', self.inputs.grey_white,
                   '-hana', self.inputs.histo_analysis,
                   '-output', self.outputs.grey,
                   '-mode', 'C', '-writeformat', 't']

        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials ?
        return command


class WhiteSurface(Step):

    def __init__(self):
        super(WhiteSurface, self).__init__()

    def _get_inputs(self):
        file_inputs = ['grey']
        other_inputs = []
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['white_surface']
 
    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_surface', 
                   self.inputs.grey,
                   self.outputs.white_surface]
        return command


class GreySurface(Step):

    def __init__(self, left=True):
        super(GreySurface, self).__init__()
        if left:
            self.inputs.side = 'left'
        else: 
            self.inputs.side = 'right'

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'split_mask', 'grey']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['grey_surface']
 
    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_grey_surface',
                   self.inputs.corrected_mri,
                   self.inputs.split_mask,
                   self.inputs.grey,
                   self.outputs.grey_surface,
                   self.inputs.side]
        return command



class Sulci(Step):

    def __init__(self, left=True):
        super(Sulci, self).__init__()
        if left:
            self.inputs.side = 'left'
        else: 
            self.inputs.side = 'right'

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'split_mask', 'grey',
                       'talairach_transformation', 'grey_white',
                       'commissure_coordinates', 'white_surface',
                       'grey_surface']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['sulci']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_sulci',
                   self.inputs.corrected_mri,
                   self.inputs.split_mask,
                   self.inputs.grey,
                   self.inputs.talairach_transformation,
                   self.inputs.grey_white,
                   self.inputs.commissure_coordinates,
                   self.inputs.white_surface,
                   self.inputs.grey_surface,
                   self.outputs.sulci,
                   self.inputs.side]
        return command


class SulciLabelling(Step):

    def __init__(self, left=True):
        super(SulciLabelling, self).__init__()
        if left:
            self.inputs.side = 'left'
        else: 
            self.inputs.side = 'right'

    def _get_inputs(self):
        file_inputs = ['sulci']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['labeled_sulci']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis_sulci_labelling',
                   self.inputs.sulci,
                   self.outputs.labeled_sulci,
                   self.inputs.side]
        return command
