import os
import getpass
import shutil

from morphologist.study import Study
from morphologist.intra_analysis import IntraAnalysis
from morphologist.tests.mocks.study import MockStudy, MockIntraAnalysisStudy

class AbstractStudyTestCase(object):

    def __init__(self):
        self.study = None
        self.study_cls = None
        self.studyname = None
        self.outputdir = None
        self.filenames = None
        self.subjectnames = None
        self.groupnames = None

    def create_study(self):
        self.study = self.study_cls(self.studyname, self.outputdir)
        return self.study

    def add_subjects(self):
        for filename, subjectname, groupname in zip(self.filenames,
                                self.subjectnames, self.groupnames):
            self.study.add_subject_from_file(filename, subjectname, groupname)

    def set_parameters(self):
        raise Exception('AbstractStudyTestCase is an abstract class')

    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template=self.parameter_template())



class MockStudyTestCase(AbstractStudyTestCase):

    '''
    -> Mock analysis
    '''

    def __init__(self):
        super(MockStudyTestCase, self).__init__()
        self.study_cls = MockStudy
        self.studyname = 'mock_study'
        self.outputdir = '/tmp'
        self.subjectnames = ['bla', 'blabla', 'blablabla'] 
        self.filenames = ['foo'] * len(self.subjectnames)
        self.groupnames = ['group1'] * len(self.subjectnames)
        self.parameter_template = 'foo' 

    def create_study(self):
        self.study = MockStudy(self.studyname, self.outputdir)
        return self.study


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

    def create_study(self):
        self.study = MockIntraAnalysisStudy(self.studyname, self.outputdir)
        print "create mock intra analysis study"
        return self.study

    def parameter_template(self):
        return IntraAnalysis.BRAINVISA_PARAM_TEMPLATE 


class FlatFilesStudyTestCase(AbstractStudyTestCase):
    prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

    def __init__(self):
        super(FlatFilesStudyTestCase, self).__init__()
        self.study_cls = Study
        self.studyname = 'my_study'
        self.outputdir = '/tmp/morphologist_tests/studies/my_study'
        basenames = ['caca.ima', 'chaos.nii.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(FlatFilesStudyTestCase.prefix,
                                  filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']

        self.parameter_template = IntraAnalysis.DEFAULT_PARAM_TEMPLATE

    def create_study(self):
        self.study = Study(self.studyname, self.outputdir)
        return self.study

    
class BrainvisaStudyTestCase(AbstractStudyTestCase):

    def __init__(self):
        super(BrainvisaStudyTestCase, self).__init__()
        self.study_cls = Study
        self.studyname = 'test'
        self.outputdir = '/volatile/laguitton/data/icbm/icbm'
        self.subjectnames = ['icbm100T', 'icbm101T']
        self.groupnames = ['group1'] * len(self.subjectnames)
        self.filenames = [os.path.join(self.outputdir, subject,
                          't1mri', 'default_acquisition',
                          '%s.ima' % subject) for subject in self.subjectnames]
        self.parameter_template = IntraAnalysis.BRAINVISA_PARAM_TEMPLATE

    def create_study(self):
        self.study =  Study(self.studyname, self.outputdir)
        return self.study

