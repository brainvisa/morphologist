from morphologist.core.subject import Subject
from morphologist.core.study import Study
from morphologist.core.tests import reset_directory, remove_file
import six


class AbstractStudyTestCase(object):

    def __init__(self):
        self.study = None
        self.analysis_type = None
        self.studyname = None
        self.output_directory = None
        self.subjectnames = None
        self.groupnames = None
        self.filenames = None

    def create_study(self):
        self.study = Study(analysis_type=self.analysis_type,
                           study_name=self.studyname,
                           output_directory=self.output_directory)
        return self.study

    def add_subjects(self):
        for subjectname, groupname, filename in zip(self.subjectnames,
                                    self.groupnames, self.filenames):
            subject = Subject(subjectname, groupname, filename)
            self.study.add_subject(subject)

    def delete_some_input_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def create_some_output_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def restore_input_files(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def step_to_wait_testcase_1(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def step_to_wait_testcase_2(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def step_to_wait_testcase_3(self):
        raise NotImplementedError("AbstractStudyTestCase is an abstract class")

    def get_a_subject_id(self):
        first_subject_id = next(six.iterkeys(self.study.subjects))
        return first_subject_id


class MockStudyTestCase(AbstractStudyTestCase):
    '''
    -> Mock analysis
    '''

    def __init__(self):
        super(MockStudyTestCase, self).__init__()
        self.analysis_type = "MockAnalysis"
        self.studyname = 'mock_study'
        self.output_directory = '/tmp/morphologist_output_mock_study_test_case'
        self.subjectnames = ['bla', 'blabla', 'blablabla'] 
        self.filenames = ['/tmp/morphologist_output_mock_study_test_case/foo'] * len(self.subjectnames)
        self.groupnames = [Subject.DEFAULT_GROUP] * len(self.subjectnames)
        reset_directory(self.output_directory)

    def delete_some_input_files(self):
        parameter_names = ['input_image']
        for name in parameter_names:
            file_name = getattr(
                self.study.analyses.values()[1].pipeline.process, name)
            remove_file(file_name)

    def create_some_output_files(self):
        parameter_names = ['output_image']
        for name in parameter_names:
            file_name = getattr(
                self.study.analyses.values()[0].pipeline.process, name)
            f = open(file_name, "w")
            f.write("something\n")
            f.close()

    def restore_input_files(self):
        # useless because the input files are created in set_analysis_parameters
        pass

    def step_to_wait_testcase_1(self):
        subject_id = self.get_a_subject_id()
        return subject_id, "step1"

    def step_to_wait_testcase_2(self):
        subject_id = self.get_a_subject_id()
        return subject_id, "step2"

    def step_to_wait_testcase_3(self):
        subject_id = self.get_a_subject_id()
        return subject_id, "step3"


class MockFailedStudyTestCase(MockStudyTestCase):

    def __init__(self):
        super(MockFailedStudyTestCase, self).__init__()
        self.failed_step_id = "step2"
        self.analysis_type = "MockFailedAnalysis"

