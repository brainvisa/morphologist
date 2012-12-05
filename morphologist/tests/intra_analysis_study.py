import os
import getpass
import shutil

from morphologist.study import Study
from morphologist.tests.study import AbstractStudyTestCase
from morphologist.intra_analysis import IntraAnalysis

class IntraAnalysisStudyTestCase(AbstractStudyTestCase):

    '''    
    -> Intra analysis    
    -> Default parameter template
    '''

    def __init__(self):
        super(IntraAnalysisStudyTestCase, self).__init__()
        self.studyname = "study with param template: " + self.parameter_template() 
        self.outputdir = os.path.join('/neurospin', 'lnao', 'Panabase', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(), 
                                      self.parameter_template())
        print self.outputdir
        if os.path.isdir(self.outputdir):
            shutil.rmtree(self.outputdir)
        os.makedirs(self.outputdir) # always starts with a clean state

        inputdir = os.path.join('/neurospin', 'lnao', 'Panabase', 
                                'cati-dev-prod', 'morphologist', 'raw_irm')
        basenames = ['caca.ima', 'chaos.nii.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(inputdir, filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']

    def study_cls(self):
        return Study

    def parameter_template(self):
        return IntraAnalysis.DEFAULT_PARAM_TEMPLATE 

    def create_study(self):
        self.study = Study(self.studyname, self.outputdir)
        return self.study


    
class MockIntraAnalysisStudyTestCase(IntraAnalysisStudyTestCase):

    '''
    -> Mock intra analysis
    -> Default parameter template
    '''

    def study_cls(self):
        return MockIntraAnalysisStudy

    def create_study(self):
        self.study = MockIntraAnalysisStudy(self.studyname, self.outputdir)
        print "create mock intra analysis"
        return self.study


class IntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):

    '''
    -> Intra analysis
    -> Brainvisa parameter template
    '''

    def parameter_template(self):
        return IntraAnalysis.BRAINVISA_PARAM_TEMPLATE 


class MockIntraAnalysisStudyTestCaseBvParamTemplate(IntraAnalysisStudyTestCase):

    '''
    -> Brainvisa parameter template
    -> Mock intra analysis
    '''

    def get_study_cls(self):
        return MockIntraAnalysisStudy

    def create_study(self):
        self.study = MockIntraAnalysisStudy(self.studyname, self.outputdir)
        return self.study

    def parameter_template(self):
        return IntraAnalysis.BRAINVISA_PARAM_TEMPLATE 



class FlatFilesStudyTestCase(AbstractStudyTestCase):
    prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

    def __init__(self):
        super(FlatFilesStudyTestCase, self).__init__()
        self.studyname = 'my_study'
        self.outputdir = '/tmp/morphologist_tests/studies/my_study'
        basenames = ['caca.ima', 'chaos.nii.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(FlatFilesStudyTestCase.prefix,
                                  filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']

        self.parameter_template = IntraAnalysis.DEFAULT_PARAM_TEMPLATE

    def study_cls(self):
        return Study

    def create_study(self):
        self.study = Study(self.studyname, self.outputdir)
        return self.study

    
class BrainvisaStudyTestCase(AbstractStudyTestCase):

    def __init__(self):
        super(BrainvisaStudyTestCase, self).__init__()
        self.studyname = 'test'
        self.outputdir = '/volatile/laguitton/data/icbm/icbm'
        self.subjectnames = ['icbm100T', 'icbm101T']
        self.groupnames = ['group1'] * len(self.subjectnames)
        self.filenames = [os.path.join(self.outputdir, subject,
                          't1mri', 'default_acquisition',
                          '%s.ima' % subject) for subject in self.subjectnames]
        self.parameter_template = IntraAnalysis.BRAINVISA_PARAM_TEMPLATE

    def study_cls(self):
        return Study

    def create_study(self):
        self.study =  Study(self.studyname, self.outputdir)
        return self.study

