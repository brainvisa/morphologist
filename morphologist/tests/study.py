import os

from morphologist.study import Study
from morphologist.intra_analysis import IntraAnalysis
from morphologist.tests.mocks.study import MockStudy

class AbstractStudyTestCase(object):

    def __init__(self):
        self.study = None
        self.studyname = None
        self.outputdir = None
        self.filenames = None
        self.subjectnames = None
        self.groupnames = None

    def create_study(self):
        raise Exception('AbstractStudyTestCase is an abstract class')

    def add_subjects(self):
        for filename, subjectname, groupname in zip(self.filenames,
                                self.subjectnames, self.groupnames):
            self.study.add_subject_from_file(filename, subjectname, groupname)

    def set_parameters(self):
        raise Exception('AbstractStudyTestCase is an abstract class')


class MockStudyTestCase(AbstractStudyTestCase):

    def __init__(self):
        super(MockStudyTestCase, self).__init__()
        self.studyname = 'mock_study'
        self.outputdir = '/tmp'
        self.subjectnames = ['bla', 'blabla', 'blablabla'] 
        self.filenames = ['foo'] * len(self.subjectnames)
        self.groupnames = ['group1'] * len(self.subjectnames)
 
    def create_study(self):
        self.study = MockStudy(self.studyname, self.outputdir)
        return self.study
 
    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template='foo')
 

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

    def create_study(self):
        self.study = Study(self.studyname, self.outputdir)
        return self.study

    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template=IntraAnalysis.DEFAULT_PARAM_TEMPLATE)


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

    def create_study(self):
        self.study =  Study(self.studyname, self.outputdir)
        return self.study

    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template=IntraAnalysis.BRAINVISA_PARAM_TEMPLATE)

