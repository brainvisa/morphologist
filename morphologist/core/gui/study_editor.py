import os
from collections import namedtuple

from morphologist.core.analysis import ImportationError


class StudyEditor(object):
    # study edition mode
    NEW_STUDY = 0
    EDIT_STUDY = 1
    # update policy
    ON_SUBJECT_REMOVED_DELETE_FILES = 0
    ON_SUBJECT_REMOVED_DO_NOTHING = 1

    def __init__(self, study, mode=NEW_STUDY,
        study_update_policy=ON_SUBJECT_REMOVED_DO_NOTHING):
        self.study = study
        self.study_update_policy = study_update_policy 
        self._study_properties_editor = StudyPropertiesEditor(study)
        self._subjects_editor = SubjectsEditor(study)
        self.mode = mode

    @property
    def subjects_editor(self):
        return self._subjects_editor

    @property
    def study_properties_editor(self):
        return self._study_properties_editor

    def create_updated_study(self):
        self._study_properties_editor.update_study(self.study)
        self._subjects_editor.update_study(self.study, \
                                self.study_update_policy)
        return self.study
    

class StudyPropertiesEditor(object):
    # check status to build a study
    STUDY_PROPERTIES_VALID = 0x0
    OUTPUTDIR_NOT_EXISTS = 0x1
    OUTPUTDIR_NOT_EMPTY = 0x2
    BACKUP_FILENAME_DIR_NOT_EXISTS = 0x4
    BACKUP_FILENAME_EXISTS = 0x8
    
    def __init__(self, study):
        self.name = study.name
        self.outputdir = study.outputdir
        self.backup_filename = study.backup_filename
        self.parameter_templates = study.analysis_cls().PARAMETER_TEMPLATES
        self.parameter_template_index = self.parameter_templates.index(study.parameter_template.__class__)

    def update_study(self, study):
        study.name = self.name
        study.outputdir = self.outputdir
        study.backup_filename = self.backup_filename
        parameter_template = self.parameter_templates[self.parameter_template_index]
        study.parameter_template = study.analysis_cls().create_parameter_template(parameter_template.name, 
                                                                                  self.outputdir)

    def get_consistency_status(self, editor_mode):
        if editor_mode == StudyEditor.NEW_STUDY:
            status = self._outputdir_consistency_status()
            status |= self._backup_filename_consistency_status()
        elif editor_mode == StudyEditor.EDIT_STUDY:
            status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        return status

    def _outputdir_consistency_status(self):
        status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        if not os.path.exists(self.outputdir):
            status |= StudyPropertiesEditor.OUTPUTDIR_NOT_EXISTS
        elif len(os.listdir(self.outputdir)) != 0:
            status |= StudyPropertiesEditor.OUTPUTDIR_NOT_EMPTY
        return status
            
    def _backup_filename_consistency_status(self):
        status = StudyPropertiesEditor.STUDY_PROPERTIES_VALID
        backup_filename_directory = os.path.dirname(self.backup_filename)
        if not os.path.exists(backup_filename_directory):
            status |= StudyPropertiesEditor.BACKUP_FILENAME_DIR_NOT_EXISTS
        elif os.path.exists(self.backup_filename):
            status |= StudyPropertiesEditor.BACKUP_FILENAME_EXISTS
        return status
 
 
class SubjectsEditor(object):
    IdentifiedSubject = namedtuple('SubjectOrigin', ['id', 'subject'])
   
    def __init__(self, study):
        self._subjects_origin = []
        self._subjects = []
        self._removed_subjects_id = []
        self._similar_subjects_n = {}
        # FIXME: store this information in ImportationError
        self._has_imported_some_subjects = False
        for subject_id, subject in study.subjects.iteritems():
            subject_copy = subject.copy()
            self._subjects.append(subject_copy)
            origin = self.IdentifiedSubject(subject_id, subject)
            self._subjects_origin.append(origin)
            self._similar_subjects_n.setdefault(subject_id, 0)
            self._similar_subjects_n[subject_id] += 1

    def __len__(self):
        return len(self._subjects)

    def __getitem__(self, index): 
        return self._subjects[index]

    def __delitem__(self, index): 
        subject = self._subjects[index]
        subject_id = subject.id()
        self._similar_subjects_n[subject_id] -= 1
        if self._similar_subjects_n[subject_id] == 0:
            del self._similar_subjects_n[subject_id]
        origin = self._subjects_origin[index]
        if origin is not None:
            self._removed_subjects_id.append(origin.id)
        del self._subjects_origin[index]
        del self._subjects[index]

    def __iter__(self):
        for subject in self._subjects:
            yield subject

    def append(self, subject):
        self._subjects.append(subject)
        self._subjects_origin.append(None)
        subject_id = subject.id()
        self._similar_subjects_n.setdefault(subject_id, 0)
        self._similar_subjects_n[subject_id] += 1

    def is_ith_subject_duplicated(self, index):
        subject = self._subjects[index]
        subject_id = subject.id()
        return self._similar_subjects_n[subject_id] != 1

    def is_ith_subject_new(self, index):
        return self._subjects_origin[index] is None

    def update_ith_subject_property(self, index, property, value):
        subject = self._subjects[index] 
        old_subject_id = subject.id()
        subject.__setattr__(property, value)
        new_subject_id = subject.id()
        self._similar_subjects_n[old_subject_id] -= 1
        if self._similar_subjects_n[old_subject_id] == 0:
            del self._similar_subjects_n[old_subject_id]
        self._similar_subjects_n.setdefault(new_subject_id, 0)
        self._similar_subjects_n[new_subject_id] += 1

    def update_study(self, study, study_update_policy):
        # XXX: operations order is important : del, rename, add
        for subject_id in self._removed_subjects_id:
            self._removed_subjects_from_study(study,
                        subject_id, study_update_policy)

        if len(self._renamed_subjects()):
            assert(0) # existing subjects can't be renamed from GUI
 
        subjects_importation_failed = []
        for subject in self._added_subjects():
            try:
                study.add_subject(subject)
            except ImportationError, e:
                subjects_importation_failed.append(subject)
            else:
                self._has_imported_some_subjects = True
        if subjects_importation_failed:
            str_subjects = []
            for subject in subjects_importation_failed:
                str_subjects.append(str(subject))
            raise ImportationError("The importation failed for the " + \
                "following subjects:\n%s." % ", ".join(str_subjects))

    def _added_subjects(self):
        added_subjects = []
        for index, _ in enumerate(self):
            subject = self._subjects[index]
            origin = self._subjects_origin[index]
            if origin is None:
                added_subjects.append(subject)
        return added_subjects

    def _renamed_subjects(self):
        renamed_subjects = []
        for index, _ in enumerate(self):
            subject = self._subjects[index]
            origin = self._subjects_origin[index]
            if origin is None: continue
            if subject != origin.subject:
                renamed_subjects.append((origin, subject))
        return renamed_subjects

    def has_subjects_to_be_removed(self):
        return len(self._removed_subjects_id)

    # FIXME: store this information in ImportationError
    def has_imported_some_subjects(self):
        return self._has_imported_some_subjects

    def _removed_subjects_from_study(self, study, subject_id,
                                        study_update_policy):
        if study_update_policy == StudyEditor.ON_SUBJECT_REMOVED_DELETE_FILES:
            study.remove_subject_and_files_from_id(subject_id)
        elif study_update_policy == StudyEditor.ON_SUBJECT_REMOVED_DO_NOTHING:
            study.remove_subject_from_id(subject_id)
        else:
            assert(0)

    def are_some_subjects_duplicated(self):
        for n in self._similar_subjects_n.values():
            if n != 1: return True
        return False
 
