import os

from morphologist.study import Study


class AbstractStudyTestCase(object):

    def __init__(self):
        self.study = None
        self.studyname = None
        self.outputdir = None
        self.filenames = None
        self.subjectnames = None
        self.groupnames = None

    def create_study(self):
        self.study = Study(self.studyname, self.outputdir)
        for filename, subjectname, groupname in zip(self.filenames,
                                self.subjectnames, self.groupnames):
            self.study.add_subject_from_file(filename, subjectname, groupname)
        return self.study

    # FIXME : why clear results ?
    def create_and_clear_study(self):
        study = self.create_study()
        study.clear_results()
        return study


class FlatFilesStudyTestCase(AbstractStudyTestCase):
    prefix = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm'

    def __init__(self):
        super(FlatFilesStudyTestCase, self).__init__()
        self.studyname = 'my_study'
        self.outputdir = '/neurospin/lnao/Panabase/cati-dev-prod/morphologist/studies/my_study'
        basenames = ['caca.ima', 'chaos.ima.gz',
                     'dionysos2.ima', 'hyperion.nii']
        self.filenames = [os.path.join(FlatFilesStudyTestCase.prefix,
                                  filename) for filename in basenames]
        self.subjectnames = ['caca', 'chaos', 'dionysos2', 'hyperion']
        self.groupnames = ['group 1', 'group 2', 'group 3', 'group 4']


class BrainvisaStudyTestCase(object):

    def __init__(self):
        super(BrainvisaStudyTestCase, self).__init__()
        self.studyname = 'test'
        self.outputdir = '/volatile/laguitton/data/icbm/icbm'
        self.subjectnames = ['icbm100T', 'icbm101T']
        self.filenames = [os.path.join(outputdir, subject,
                          't1mri', 'default_acquisition',
                          '%s.ima' % subject) for subject in self.subjectnames]
