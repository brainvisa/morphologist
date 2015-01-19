from morphologist.core.steps import Step
from morphologist.intra_analysis import constants


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
        command = ["python", "-m",
                   "brainvisa.tools.data_management.image_importation",
                   self.inputs.input, 
                   self.outputs.output]
        return command
    
    
class SpatialNormalization(Step):

    def __init__(self):
        super(SpatialNormalization, self).__init__()
        self.name = 'normalization'
        self.description = "<h4>Spatial normalization using SPM8 standalone.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p>You should check your SPM installation.</p>
<p>The normalization step is using SPM8, preferably the standalone version, which is compiled and does not need Matlab. Alternatively, Morphologist should be able to use the Matlab-based regular SPM8.</p>
<p>SPM8 has to be installed, and properly configured. The configuration is currently taken from BrainVisa configuration, so you should do the following:
<ul>
<li><b><a href="http://brainvisa.info">Open the brainvisa software</a></b></li>
<li>In brainvisa, go to the 'BrainVISA/Preferences' menu, in the SPM tab</li>
<li>Set paths for your SPM installation. There is an 'auto detect' button there, you can try it.</li>
<li>Validate the preferences in BrainVisa</li>
</ul></p>
<p>If the Matlab-based SPM is correctly installed and configured, and the normalization step still does not run, you may also check that <b>Matlab</b> is correcly configured, also in <b>BrainVisa preferences</b>, in the <b>Matlab tab</b>.</p>
<p>If the Matlab-based SPM still does not work at this point, you may check whether Matlab is working: you may encounter Matlab licence issues.</p>
"""

    def _get_inputs(self):
        file_inputs = ['mri']
        other_inputs = []
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['commissure_coordinates', 'talairach_transformation']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.normalization',
                   self.inputs.mri, 
                   self.outputs.commissure_coordinates, 
                   self.outputs.talairach_transformation]
        return command
    
        
class BiasCorrection(Step):

    def __init__(self):
        super(BiasCorrection, self).__init__()
        self.name = 'bias_correction'
        self.inputs.fix_random_seed = False
        self.description = "<h4>Bias correction using VipT1BiasCorrection.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipT1BiasCorrection command may not be found.</li>
<li>Bias correction failure might be due to an inappropriate input image:
  <ul><li>Has the raw T1 image been correctly imported by Morphologist ? After import it should be in NIFTI-1 format, voxels should be short ints (16 bits), and the values range should be positive and not too close to the upper bound (32737).</li>
  <li>Currently only resolutions around 1mm are supported (typically 256x256x128 voxels). If your image has a higher resolution, like 0.5mm with 512x512 voxels per slice, it might cause problems.</li>
  </ul>
</li>
<li>In other situations, the raw T1 image quality might be in cause...</li>
</ul></p>
"""

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
        self.name = 'histogram_analysis'
        self.inputs.fix_random_seed = False
        self.description = "<h4>Histogram analysis using VipHistoAnalysis.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipHistoAnalysis command may not be found.</li>
<li>Check that the <b>bias correction step</b> has produced reasonable results. An incomplete inhomogeneity correction can make it very difficult to analyze the histogram and find the grey and white matters average values. It is the most probable cause of problems in the Morphologist pipeline.</li>
<li>In some (hopfully unfrequent) situations, it may help to manually correct the analysis by manually setting values in the <b>.han file</b>. A future version of Morphologist will provide a nice editor for this.</li>
</ul></p>
"""

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
        self.name = 'brain_segmentation'
        self.inputs.erosion_size = 1.8
        self.inputs.fix_random_seed = False
        self.description = "<h4>Brain segmentation using VipGetBrain.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipGetBrain command may not be found.</li>
<li>The most probable cause of error at this step is an unsatisfying result for the <b>bias correction step</b>, which in turn would cause a wrong <b>histogram analysis step</b>.</li>
<li>In low quality images, the brain mask output may be present but inaccurate. In case of local artifacts, some manual corrections may help.</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'edges', 'variance', 'histo_analysis', 'white_ridges']
        other_inputs = ['erosion_size', 'fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['brain_mask']
 
    def get_command(self):
        command = ['VipGetBrain',
                   '-i', self.inputs.corrected_mri,
                   '-Points', self.inputs.commissure_coordinates,
                   '-berosion', str(self.inputs.erosion_size),
                   '-Edgesname', self.inputs.edges,
                   '-Variancename', self.inputs.variance,
                   '-hname',  self.inputs.histo_analysis,
                   '-bname', self.outputs.brain_mask,
                   '-Ridge', self.inputs.white_ridges,
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
        self.name = 'split_brain'
        self.inputs.bary_factor = 0.6
        self.inputs.fix_random_seed = False
        self.description = "<h4>Split brain using VipSplitBrain.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipSplitBrain command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Check the <b>normalization step</b>: orientation in a common Talairach box is used in this step to localize and break the corpus callosum. If the orientation is not correctly determined, this split may fail.</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'brain_mask', 'white_ridges', 'histo_analysis']
        other_inputs = ['bary_factor', 'fix_random_seed']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['split_mask']
   
    def get_command(self):
        command = ['VipSplitBrain',
                   '-input', self.inputs.corrected_mri,
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

    def __init__(self, side):
        super(GreyWhite, self).__init__()
        self.name = 'grey_white'
        self.inputs.side = side
        self.inputs.fix_random_seed = False
        self.description = "<h4>Grey and white matter segmentation using VipGreyWhiteClassif.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipGreyWhiteClassif command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Otherwise, the input image quality may be in cause.</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'commissure_coordinates',
                       'histo_analysis', 'split_mask', 'edges']
        other_inputs = ['fix_random_seed', 'side']
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
        if self.inputs.side == constants.LEFT:
            label = '2'
        elif self.inputs.side == constants.RIGHT:
            label = '1'
        else:
            assert(0)
        command.extend(['-label', label, '-output', self.outputs.grey_white])
        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials ?
        return command


class Grey(Step):

    def __init__(self):
        super(Grey, self).__init__()
        self.name = 'grey'
        self.inputs.fix_random_seed = False
        self.description = "<h4>Grey mask computation using VipHomotopic.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipHomotopic command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Otherwise, this step should not fail...</li>
</ul></p>
"""

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
                   '-mode', 'C', '-writeformat', 't',
                   '-version', '2' ]

        if self.inputs.fix_random_seed:
            command.extend(['-srand', '10'])  
        # TODO referentials ?
        return command


class WhiteSurface(Step):

    def __init__(self):
        super(WhiteSurface, self).__init__()
        self.name = 'white_surface'
        self.description = "<h4>White surface using morphologist.intra_analysis.commands.surface.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['grey']
        other_inputs = []
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['white_surface']
 
    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.surface',
                   self.inputs.grey,
                   self.outputs.white_surface]
        return command


class GreySurface(Step):

    def __init__(self, side):
        super(GreySurface, self).__init__()
        self.name = 'grey_surface'
        self.inputs.side = side
        self.description = "<h4>Grey surface using morphologist.intra_analysis.commands.grey_surface.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'split_mask', 'grey']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['grey_surface']
 
    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.grey_surface',
                   self.inputs.corrected_mri,
                   self.inputs.split_mask,
                   self.inputs.grey,
                   self.outputs.grey_surface,
                   self.inputs.side]
        return command



class Sulci(Step):

    def __init__(self, side):
        super(Sulci, self).__init__()
        self.name = 'sulci'
        self.inputs.side = side
        self.description = "<h4>Sulci extraction using morphologist.intra_analysis.commands.sulci.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['corrected_mri', 'split_mask', 'grey',
                       'talairach_transformation', 'grey_white',
                       'commissure_coordinates', 'white_surface',
                       'grey_surface']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['sulci', 'sulci_data']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.sulci',
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

    def __init__(self, side):
        super(SulciLabelling, self).__init__()
        self.name = 'sulci_labelling'
        self.inputs.side = side
        self.description = "<h4>Sulci labelling using morphologist.intra_analysis.commands.sulci_labelling.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Also check that the <b>sulci SPAM models</b> are correctly downloaded and installed. To do so:
  <ul><li>open the <b>brainvisa</b> software</li>
  <li>Select the <b>Morphologist</b> toolbox, then open the <b>"Sulci/Recognition"</b> folders</li>
  <li>Select and open the <b>"SPAM models installation"</b> process</li>
  <li>Run the process</li>
  </ul>
</li>
<li>In other situations, this step should not fail...</li>
</ul></p>
"""

    def _get_inputs(self):
        file_inputs = ['sulci']
        other_inputs = ['side']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['labeled_sulci', 'labeled_sulci_data']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.sulci_labelling',
                   self.inputs.sulci,
                   self.outputs.labeled_sulci,
                   self.inputs.side]
        return command


class Morphometry(Step):

    def __init__(self, side, normalized):
        super(Morphometry, self).__init__()
        self.name = 'morphometry'
        self.inputs.side = side
        self.inputs.normalized = normalized
        self.description = "<h4>Morphometry using morphologist.intra_analysis.commands.morphometry.</h4>"
        self.help_message = '' #TODO

    def _get_inputs(self):
        file_inputs = ['labeled_sulci']
        other_inputs = ['side', 'normalized']
        return file_inputs, other_inputs

    def _get_outputs(self):
        return ['morphometry']

    def get_command(self):
        command = ['python', '-m', 'morphologist.intra_analysis.commands.morphometry',
                   self.inputs.labeled_sulci,
                   self.inputs.side,
                   self.outputs.morphometry]
        if self.inputs.normalized:
            command.append('--normalized')
        return command
