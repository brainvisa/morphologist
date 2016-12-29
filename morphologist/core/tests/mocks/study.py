
import os
import re
import glob

from morphologist.core.study import Study
from morphologist.core.subject import Subject
from morphologist.core.analysis import AnalysisFactory


class MockStudy(Study):

    def __init__(self, *args, **kwargs):
        super(MockStudy, self).__init__(*args, **kwargs)

    def get_subjects_from_pattern(self, exact_match=False,
                                  progress_callback=None):
        subjects = []
        glob_pattern = os.path.join(
            self.output_directory, "*_input.nii")
        regexp = re.compile(
            "^" + os.path.join(self.output_directory,
                               "([^-]+)-(.+)_input\.(?:nii)$"))

        for filename in glob.iglob(glob_pattern):
            match = regexp.match(filename)
            if match:
                groupname = match.group(1)
                subjectname = match.group(2)
                subject = Subject(subjectname, groupname, filename)
                subjects.append(subject)
        return subjects

