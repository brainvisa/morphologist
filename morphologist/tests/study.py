
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
        self.study = self.study_cls(self.studyname, self.outputdir)
        return self.study

    def study_cls(self):
        raise Exception('AbstractStudyTestCase is an abstract class')

    def add_subjects(self):
        for filename, subjectname, groupname in zip(self.filenames,
                                self.subjectnames, self.groupnames):
            self.study.add_subject_from_file(filename, subjectname, groupname)

    def parameter_template(self):
        raise Exception('AbstractStudyTestCase is an abstract class')

    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template=self.parameter_template())



class MockStudyTestCase(AbstractStudyTestCase):

    '''
    -> Mock analysis
    '''

    def __init__(self):
        super(MockStudyTestCase, self).__init__()
        self.studyname = 'mock_study'
        self.outputdir = '/tmp'
        self.subjectnames = ['bla', 'blabla', 'blablabla'] 
        self.filenames = ['foo'] * len(self.subjectnames)
        self.groupnames = ['group1'] * len(self.subjectnames)

    def study_cls(self):
        return MockStudy

    def create_study(self):
        self.study = MockStudy(self.studyname, self.outputdir)
        return self.study

    def parameter_template(self):
        return 'foo'


