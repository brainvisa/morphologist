import os
import json
import re
import glob

from morphologist.core.utils import OrderedDict
from morphologist.core.analysis \
    import AnalysisFactory, Parameters, ImportationError
from morphologist.core.constants import ALL_SUBJECTS
from morphologist.core.subject import Subject

# CAPSUL
from capsul.study_config import StudyConfig

import traits.api as traits


STUDY_FORMAT_VERSION = '0.5'


class Study(StudyConfig):
    default_output_directory = os.path.join(
        os.path.expanduser("~"), 'morphologist/studies/study')

    def __init__(self, analysis_type, study_name="undefined study",
                 output_directory=default_output_directory):
        default_config = {
            "use_soma_workflow": True,
            "somaworkflow_computing_resource": "localhost",
            "study_name": study_name,
            "input_fom": "morphologist-auto-nonoverlap-1.0",
            "output_fom": "morphologist-auto-nonoverlap-1.0",
            "shared_fom": "shared-brainvisa-1.0",
            "output_directory": output_directory,
            "input_directory": output_directory,
            "volumes_format": "NIFTI",
            "meshes_format": "GIFTI",
        }
        super(Study, self).__init__(init_config=default_config,
            modules=StudyConfig.default_modules + \
            ['BrainVISAConfig', 'FSLConfig', 'FomConfig'])

        # study_name is marked as transient in StudyConfig. I don't know why.
        self.trait('study_name').transient = False

        self.analysis_type = analysis_type # string : name of the analysis class
        self.add_trait("subjects", traits.Trait(OrderedDict()))
        self.subjects = OrderedDict()
        self.template_pipeline = None
        self.analyses = {}
        self.on_trait_change(self._force_input_dir, 'output_directory')

    def _force_input_dir(self, value):
        self.input_directory = value

    def analysis_cls(self):
        return AnalysisFactory.get_analysis_cls(self.analysis_type)

    def _create_analysis(self):
        return AnalysisFactory.create_analysis(
            self.analysis_type, self)

    @property 
    def backup_filepath(self):
        return self._get_backup_filepath_from_output_directory(
            self.output_directory)

    @staticmethod
    def _get_backup_filepath_from_output_directory(output_directory):
        return os.path.join(output_directory, 'study.json')

    @staticmethod
    def _get_output_directory_from_backup_filepath(backup_filepath):
        return os.path.dirname(backup_filepath)

    @classmethod
    def from_file(cls, backup_filepath):
        output_directory = \
            cls._get_output_directory_from_backup_filepath(backup_filepath)
        try:
            with open(backup_filepath, "r") as fd:
                    serialized_study = json.load(fd)
        except Exception, e:
            raise StudySerializationError("%s" %(e))
        try:
            study = cls.unserialize(serialized_study, output_directory)
        except KeyError, e:
            print e
            raise
            raise StudySerializationError("file content does not "
                                          "match with study file format.")
        return study

    @classmethod
    def unserialize(cls, serialized, output_directory):
        try:
            version = serialized['study_format_version']
        except:
            msg = "unknown study format version"
            raise StudySerializationError(msg)
        if version != STUDY_FORMAT_VERSION:
            msg = "find unsupported study format version '%s'" % version
            raise StudySerializationError(msg)
        study = cls(analysis_type=serialized['analysis_type'], 
                    study_name=serialized['study_name'],
                    output_directory=output_directory)
        serialized_dict = dict(
            [(key, value) for key, value in serialized.iteritems()
             if key not in ('subjects', 'study_format_version',
                            'analysis_type', 'inputs', 'outputs')])
        study.set_study_configuration(serialized_dict)
        for subject_id, serialized_subject in \
                serialized['subjects'].iteritems():
            subject = Subject.unserialize(
                serialized_subject, study.output_directory)
            study.subjects[subject_id] = subject
        for subject_id, subject in study.subjects.iteritems():
            if subject_id not in serialized['inputs']:
                raise StudySerializationError("Cannot find input params"
                                         " for subject %s" % str(subject))
            if subject_id not in serialized['outputs']:
                raise StudySerializationError("Cannot find output params" 
                                         " for subject %s" % str(subject))
            serialized_inputs = serialized['inputs'][subject_id] 
            serialized_outputs = serialized['outputs'][subject_id]
            inputs = {}
            outputs = {}
            analysis = study._create_analysis()
            analysis.inputs = inputs
            analysis.outputs = outputs
            analysis.subject = subject
            study.analyses[subject_id] = analysis
        return study

    @classmethod
    def from_study_directory(cls, study_directory):
        backup_filepath = \
            cls._get_backup_filepath_from_output_directory(study_directory)
        return cls.from_file(backup_filepath)

    @classmethod
    def from_organized_directory(cls, analysis_type, organized_directory):
        study_name = os.path.basename(organized_directory)
        new_study = cls(
            analysis_type, study_name=study_name,
            output_directory=organized_directory)
        subjects = new_study.get_subjects_from_pattern(exact_match=True)
        for subject in subjects:
            new_study.add_subject(subject, import_data=False)
        return new_study

    def save_to_backup_file(self):
        serialized_study = self.serialize()
        try:
            with open(self.backup_filepath, "w") as fd:
                json.dump(serialized_study, fd, indent=4, sort_keys=True)
        except Exception, e:
            raise StudySerializationError("%s" %(e))

    def serialize(self):
        if self.input_directory != self.output_directory:
            print '** WARNING: input_directory != output_directory'
            print 'input: ', self.input_directory
            print 'output:', self.output_directory
        serialized = self.export_to_dict(
            exclude_undefined=True, exclude_none=True, exclude_transient=True,
            exclude_empty=True, dict_class=dict)
        serialized['study_format_version'] = STUDY_FORMAT_VERSION
        serialized['analysis_type'] = self.analysis_type
        serialized['subjects'] = {}
        for subject_id, subject in self.subjects.iteritems():
            serialized['subjects'][subject_id] = \
                subject.serialize(self.output_directory)
        serialized['inputs'] = {}
        serialized['outputs'] = {}
        for subject_id, analysis in self.analyses.iteritems():
            serialized['inputs'][subject_id] = \
                {}
            serialized['outputs'][subject_id] = \
                {}
        return serialized 

    def add_subject(self, subject, import_data=True):
        subject_id = subject.id()
        if subject_id in self.subjects:
            raise SubjectExistsError(subject)
        self.subjects[subject_id] = subject
        self.analyses[subject_id] = self._create_analysis()
        self.analyses[subject_id].set_parameters(subject)
        if import_data:
            self._import_subject(subject_id, subject)

    def _import_subject(self, subject_id, subject):
        try:
            new_imgname = self.analyses[subject_id].import_data(subject)
        except ImportationError:
            del self.subjects[subject_id]
            del self.analyses[subject_id]
            raise ImportationError(
                "Importation failed for the following subject: %s."
                % str(subject))
        else:
            subject.filename = new_imgname

    def remove_subject_and_files_from_id(self, subject_id):
        subject = self.subjects[subject_id]
        self.remove_dirs(subject_id)
        self.remove_subject_from_id(subject_id)

    def remove_subject_from_id(self, subject_id):
        del self.subjects[subject_id]
        del self.analyses[subject_id]

    def has_subjects(self):
        return len(self.subjects) != 0

    def has_some_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
            if analysis.has_some_results():
                return True
        return False

    def has_all_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
            if not analysis.has_all_results():
                return False
        return True

    def clear_results(self, subject_ids=ALL_SUBJECTS):
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self.subjects
        for subject_id in subject_ids:
            analysis = self.analyses[subject_id]
            analysis.clear_results()

    def remove_dirs(self, subject_id):
        analysis = self.analyses[subject_id]
        analysis.remove_subject_dir()

    def get_available_computing_resources(self):
        from soma_workflow import configuration
        import socket
        config_file_path = configuration.Configuration.search_config_path()
        resource_list = configuration.Configuration.get_configured_resources(
            config_file_path)
        hostname = socket.gethostname()
        if hostname not in resource_list:
            resource_list.insert(0, hostname)
        return resource_list

    def __repr__(self):
        s = 'study_name :' + str(self.study_name) + '\n'
        s += 'output_directory :' + str(self.output_directory) + '\n'
        s += 'subjects :' + repr(self.subjects) + '\n'
        return s

    def get_subjects_from_pattern(self, exact_match=False):
        subjects = []
        MODALITY = 't1mri'
        ACQUISITION = 'default_acquisition'
        any_dir = "([^/]+)"
        if exact_match:
            glob_pattern = os.path.join(
                self.output_directory, "*", "*", MODALITY, ACQUISITION,
                "*.nii")
            regexp = re.compile(
                "^"+os.path.join(self.output_directory, any_dir, any_dir,
                                 MODALITY, ACQUISITION,
                                 "\\2\.(?:nii)$"))

        else:
            glob_pattern = os.path.join(
                self.output_directory, "*", "*", MODALITY, "*", "*.*")
            regexp = re.compile(
                "^" + os.path.join(
                    self.output_directory, any_dir, any_dir, MODALITY,
                    any_dir, "\\2\.(?:(?:nii(?:\.gz)?)|(?:ima))$"))
        for filename in glob.iglob(glob_pattern):
            match = regexp.match(filename)
            if match:
                groupname = match.group(1)
                subjectname = match.group(2)
                subject = Subject(subjectname, groupname, filename)
                subjects.append(subject)
        return subjects


class StudySerializationError(Exception):
    pass

class SubjectExistsError(Exception):
    pass
