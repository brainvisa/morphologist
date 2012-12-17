import shutil
import os.path

from morphologist.intra_analysis import IntraAnalysis
from morphologist.intra_analysis import BrainvisaIntraAnalysisParameterTemplate
from morphologist.tests.mocks.intra_analysis_steps import MockBiasCorrection, MockHistogramAnalysis, MockBrainSegmentation, MockSplitBrain


class MockIntraAnalysis(IntraAnalysis):

    def __init__(self):
        super(MockIntraAnalysis, self).__init__()
        self._init_steps()   


    def _init_steps(self):
        mock_out_files = BrainvisaIntraAnalysisParameterTemplate.get_output_params("hyperion",
                        "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/test")
        self._bias_correction = MockBiasCorrection(mock_out_files)
        self._histogram_analysis = MockHistogramAnalysis(mock_out_files)
        self._brain_segmentation = MockBrainSegmentation(mock_out_files)
        self._split_brain = MockSplitBrain(mock_out_files)  
        self._steps = [self._bias_correction, 
                       self._histogram_analysis, 
                       self._brain_segmentation, 
                       self._split_brain] 

    @classmethod
    def import_data(cls, parameter_template, filename, subjectname, outputdir):
        target_filename = cls.get_mri_path(parameter_template, 
                                  subjectname,
                                  outputdir)
        cls.create_outputdirs(parameter_template, subjectname, outputdir)
        source_filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"
        shutil.copy(source_filename, target_filename)
        # TODO remove after normalization step done
        apcfile, ext = os.path.splitext(target_filename)
        while (ext != ""):
            apcfile, ext = os.path.splitext(apcfile)
        apcfile = apcfile + ".APC"
        APC_source_filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.APC"
        APC_target_filename = os.path.join(os.path.dirname(target_filename),
                                            os.path.basename(apcfile))
        shutil.copy(APC_source_filename, APC_target_filename)
        ####################
        return target_filename



