import os

from morphologist.tests.mocks.study import MockStudy
from morphologist.tests import reset_directory, remove_file

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
        raise NotImplementedError('AbstractStudyTestCase is an abstract class')

    def add_subjects(self):
        for filename, subjectname, groupname in zip(self.filenames,
                                self.subjectnames, self.groupnames):
            self.study.add_subject_from_file(filename, subjectname, groupname)

    def parameter_template(self):
        raise NotImplementedError('AbstractStudyTestCase is an abstract class')

    def set_parameters(self):
        self.study.set_analysis_parameters(parameter_template=self.parameter_template())

    def delete_some_input_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def create_some_output_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def restore_input_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")


class MockStudyTestCase(AbstractStudyTestCase):

    '''
    -> Mock analysis
    '''

    def __init__(self):
        super(MockStudyTestCase, self).__init__()
        self.studyname = 'mock_study'
        self.outputdir = '/tmp/morphologist_output_mock_study_test_case'
        self.subjectnames = ['bla', 'blabla', 'blablabla'] 
        self.filenames = ['foo'] * len(self.subjectnames)
        self.groupnames = ['group1'] * len(self.subjectnames)
        reset_directory(self.outputdir)

    def study_cls(self):
        return MockStudy

    def create_study(self):
        self.study = MockStudy(self.studyname, self.outputdir)
        return self.study

    def parameter_template(self):
        return 'foo'

    def delete_some_input_files(self):
        parameter_names = ['input_2', 'input_5']
        for name in parameter_names:
            file_name = self.study.analyses.values()[1].input_params.get_value(name)
            remove_file(file_name)

    def create_some_output_files(self):
        parameter_names = ['output_1', 'output_4']
        for name in parameter_names:
            file_name = self.study.analyses.values()[0].output_params.get_value(name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def restore_input_files(self):
        # useless because the input files are created in set_analysis_parameters
        pass



