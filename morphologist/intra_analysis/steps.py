from __future__ import absolute_import
from morphologist.core.steps import StepHelp


class SpatialNormalization(StepHelp):

    def __init__(self):
        super(SpatialNormalization, self).__init__()
        self.name = 'orientation'
        self.description = "<h4>Spatial normalization using SPM8 or SPM12 standalone.</h4>"
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
<p>If the Matlab-based SPM is correctly installed and configured, and the normalization step still does not run, you may also check that <b>Matlab</b> is correctly configured, also in <b>BrainVisa preferences</b>, in the <b>Matlab tab</b>.</p>
<p>If the Matlab-based SPM still does not work at this point, you may check whether Matlab is working: you may encounter Matlab licence issues.</p>
"""


class BiasCorrection(StepHelp):

    def __init__(self):
        super(BiasCorrection, self).__init__()
        self.name = 'bias_correction'
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


class HistogramAnalysis(StepHelp):

    def __init__(self):
        super(HistogramAnalysis, self).__init__()
        self.name = 'histogram_analysis'
        self.description = "<h4>Histogram analysis using VipHistoAnalysis.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipHistoAnalysis command may not be found.</li>
<li>Check that the <b>bias correction step</b> has produced reasonable results. An incomplete inhomogeneity correction can make it very difficult to analyze the histogram and find the grey and white matters average values. It is the most probable cause of problems in the Morphologist pipeline.</li>
<li>In some (hopefully unfrequent) situations, it may help to manually correct the analysis by manually setting values in the <b>.han file</b>. A future version of Morphologist will provide a nice editor for this.</li>
</ul></p>
"""


class BrainSegmentation(StepHelp):

    def __init__(self):
        super(BrainSegmentation, self).__init__()
        self.name = 'brain_extraction'
        self.description = "<h4>Brain segmentation using VipGetBrain.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipGetBrain command may not be found.</li>
<li>The most probable cause of error at this step is an unsatisfying result for the <b>bias correction step</b>, which in turn would cause a wrong <b>histogram analysis step</b>.</li>
<li>In low quality images, the brain mask output may be present but inaccurate. In case of local artifacts, some manual corrections may help.</li>
</ul></p>
"""


class SplitBrain(StepHelp):

    def __init__(self):
        super(SplitBrain, self).__init__()
        self.name = 'hemispheres_split'
        self.description = "<h4>Split brain using VipSplitBrain.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipSplitBrain command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Check the <b>normalization step</b>: orientation in a common Talairach box is used in this step to localize and break the corpus callosum. If the orientation is not correctly determined, this split may fail.</li>
</ul></p>
"""
    

class GreyWhite(StepHelp):

    def __init__(self, side='left'):
        super(GreyWhite, self).__init__()
        self.name = 'grey_white_segmentation_%s' % side
        self.description = "<h4>Grey and white matter segmentation using VipGreyWhiteClassif.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipGreyWhiteClassif command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Otherwise, the input image quality may be in cause.</li>
</ul></p>
"""


class Grey(StepHelp):

    def __init__(self, side='left'):
        super(Grey, self).__init__()
        self.name = 'grey_%s' % side
        self.description = "<h4>Grey mask computation using VipHomotopic.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: the VipHomotopic command may not be found.</li>
<li>Failure may result from previous steps, especially the <b>bias correction step</b> which may have repercussions several steps later in some cases.</li>
<li>Otherwise, this step should not fail...</li>
</ul></p>
"""


class WhiteSurface(StepHelp):

    def __init__(self, side='left'):
        super(WhiteSurface, self).__init__()
        self.name = 'white_surface_%s' % side
        self.description = "<h4>White surface.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""


class GreySurface(StepHelp):

    def __init__(self, side='left'):
        super(GreySurface, self).__init__()
        self.name = 'grey_surface_%s' % side
        self.description = "<h4>Grey surface.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""


class Sulci(StepHelp):

    def __init__(self, side='left'):
        super(Sulci, self).__init__()
        self.name = 'sulci_%s' % side
        self.description = "<h4>Sulci extraction.</h4>"
        self.help_message = """<p><b>Troubleshooting:</b></p>
<p><ul><li>First, check your BrainVISA installation: some commands may not be found.</li>
<li>Normally, this step should not fail...</li>
</ul></p>
"""


class SulciLabelling(StepHelp):

    def __init__(self, side='left'):
        super(SulciLabelling, self).__init__()
        self.name = 'sulci_labelling_%s' % side
        self.description = "<h4>Sulci labelling.</h4>"
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


class Morphometry(StepHelp):

    def __init__(self):
        super(Morphometry, self).__init__()
        self.name = 'morphometry'
        self.description = "<h4>Morphometry.</h4>"
        self.help_message = '' #TODO

    #def _get_inputs(self):
        #file_inputs = ['labeled_sulci']
        #other_inputs = ['side', 'normalized']
        #return file_inputs, other_inputs

    #def _get_outputs(self):
        #return ['morphometry']

    #def get_command(self):
        #command = ['python', '-m', 'morphologist.intra_analysis.commands.morphometry',
                   #self.inputs.labeled_sulci,
                   #self.inputs.side,
                   #self.outputs.morphometry]
        #if self.inputs.normalized:
            #command.append('--normalized')
        #return command
