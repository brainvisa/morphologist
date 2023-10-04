
import os
import json
import re
import glob
import sys
import six

from morphologist.core.utils import OrderedDict
from morphologist.core.analysis \
    import AnalysisFactory, ImportationError
from morphologist.core.constants import ALL_SUBJECTS
from morphologist.core.subject import Subject

# CAPSUL
from capsul.api import Capsul
from soma.controller import Controller, Directory, undefined

# Axon config
argv = sys.argv
# Temporarily change argv[0] since it is used in neuroConfig initialization
# to set paths
sys.argv = [argv[0], '-b']
from brainvisa.configuration import axon_capsul_config_link
from brainvisa.configuration import neuroConfig
from brainvisa.axon import processes as axon_processes
# set back argv to its original value
sys.argv = argv
del argv


STUDY_FORMAT_VERSION = '1.0'


class Study(Controller, Capsul):
    default_output_directory = os.path.join(
        os.path.expanduser("~"), 'morphologist/studies/study')

    def __init__(self, analysis_type, study_name="undefined study",
                 output_directory=default_output_directory):

        def get_shared_path():
            try:
                from soma import aims
                return aims.carto.Paths.resourceSearchPath()[-1]
            except Exception:
                return '!{dataset.shared.path}'

        default_config = {
            'builtin': {
                'config_modules': [
                    'spm',
                    'axon',
                    'fsl',
                    'freesurfer',
                ],
                'dataset': {
                    'input': {
                        'path': output_directory,
                        'metadata_schema': 'brainvisa',
                    },
                    'output': {
                        'path': output_directory,
                        'metadata_schema': 'brainvisa',
                    },
                    'shared': {
                        'path': get_shared_path(),
                        'metadata_schema': 'brainvisa_shared',
                    },
                },
                'spm': {
                    'spm12_standalone': {
                        'directory': '/volatile/local/spm12-standalone',
                        'standalone': True,
                        'version': '12',
                    }
                },
                'matlab': {
                    'matlab_mcr': {
                        'mcr_directory': '/volatile/local/spm12-standalone/mcr/v97' # '/tmp/matlab_mcr/v97',
                    }
                },
            }
        }
        super().__init__(app_name=study_name)
        # make config a field in order to save it via asdict()
        config = self.config
        self.add_field('config', type_=type(config))
        self.config = config
        self.config.import_dict(default_config)

        # init/read axon config
        neuroConfig.fastStart = True
        axon_processes.initializeProcesses()
        self.axon_link = \
            axon_capsul_config_link.AxonCapsulConfSynchronizer(self)
        self.axon_link.sync_axon_to_capsul()

        self.analysis_type = analysis_type  # string : name of the analysis class
        self.add_field("subjects", type_=OrderedDict)
        #self.output_directory = output_directory
        #self.input_directory = output_directory
        self.subjects = OrderedDict()
        self.template_pipeline = None
        self.analyses = {}
        self.computing_resource = 'builtin'
        self.volumes_format = 'NIFTI gz'
        self.meshes_format = 'GIFTI'
        self.on_attribute_change.add(self._force_input_dir, 'output_directory')

    @property
    def study_name(self):
        return self.label

    @property
    def output_directory(self):
        return self.config[self.computing_resource].dataset.output.path

    @output_directory.setter
    def output_directory(self, value):
        self.config[self.computing_resource].dataset.output.path = value

    @property
    def input_directory(self):
        return self.config[self.computing_resource].dataset.input.path

    def _force_input_dir(self, value):
        self.config[self.computing_resource].dataset.input.path = value

    @property
    def somaworkflow_computing_resource(self):
        return {'builtin': 'localhost'}.get(
            self.computing_resource, self.computing_resource)

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
        except Exception as e:
            raise StudySerializationError("%s" % e)
        try:
            study = cls.unserialize(serialized_study, output_directory)
        except KeyError as e:
            print(e)
            raise
            raise StudySerializationError("file content does not "
                                          "match with study file format.")
        return study

    @classmethod
    def unserialize(cls, serialized, output_directory):
        try:
            version = serialized['study_format_version']
        except Exception:
            msg = "unknown study format version"
            raise StudySerializationError(msg)
        if version != STUDY_FORMAT_VERSION:
            msg = "find unsupported study format version '%s'" % version
            raise StudySerializationError(msg)
        study = cls(analysis_type=serialized['analysis_type'],
                    study_name=serialized['label'],
                    output_directory=output_directory)
        serialized_dict = dict(
            [(key, value) for key, value in six.iteritems(serialized)
             if key not in ('subjects', 'study_format_version',
                            'analysis_type', 'inputs', 'outputs')])
        study.import_dict(serialized_dict)
        for subject_id, serialized_subject in \
                six.iteritems(serialized['subjects']):
            subject = Subject.unserialize(
                serialized_subject, study.output_directory)
            study.subjects[subject_id] = subject
        if 'parameters' not in serialized:
            raise StudySerializationError(
                    "Cannot find parameters section in study file")
        for subject_id, subject in six.iteritems(study.subjects):
            if subject_id not in serialized['parameters']:
                raise StudySerializationError(
                    "Cannot find params for subject %s" % subject_id)
            analysis = study._create_analysis()
            analysis.subject = subject
            parameters = serialized['parameters'][subject_id]
            analysis.parameters = Study.unserialize_paths(
                parameters, study.output_directory)
            study.analyses[subject_id] = analysis
        return study

    @classmethod
    def from_study_directory(cls, study_directory):
        backup_filepath = \
            cls._get_backup_filepath_from_output_directory(study_directory)
        return cls.from_file(backup_filepath)

    @classmethod
    def from_organized_directory(cls, analysis_type, organized_directory,
                                 progress_callback=None):
        if progress_callback:
            if isinstance(progress_callback, tuple):
                callback, init_progress, scl_progess \
                    = progress_callback
            else:
                callback = progress_callback
                init_progress = 0
                scl_progess = 1.
                progress_callback = (callback, init_progress, scl_progess)
        study_name = os.path.basename(organized_directory)
        print('study class:', cls, ', dir:', organized_directory)
        new_study = cls(
            analysis_type, study_name=study_name,
            output_directory=organized_directory)
        if progress_callback:
            callback(init_progress + 0.05 * scl_progess)
            progress_callback = (callback,
                                 init_progress + .05 * scl_progess,
                                 0.25 * scl_progess)
        print('study dir:', new_study.output_directory)
        subjects = new_study.get_subjects_from_pattern(
            progress_callback=progress_callback) ##exact_match=True)
        nsubjects = len(subjects)
        for n, subject in enumerate(subjects):
            new_study.add_subject(subject, import_data=False)
            if progress_callback:
                callback(init_progress
                         + (.3 + 0.7 * (n + 1) / nsubjects) * scl_progess)
        return new_study

    def save_to_backup_file(self):
        serialized_study = self.serialize()
        try:
            with open(self.backup_filepath, "w") as fd:
                json.dump(serialized_study, fd, indent=4, sort_keys=True)
        except Exception as e:
            raise StudySerializationError("%s" %(e))

    def serialize(self):
        if self.input_directory != self.output_directory:
            print('** WARNING: input_directory != output_directory')
            print('input: ', self.input_directory)
            print('output:', self.output_directory)
        serialized = self.asdict(dict_factory=dict, exclude_empty=True,
                                 exclude_none=True)
        serialized['label'] = self.label
        serialized['study_format_version'] = STUDY_FORMAT_VERSION
        serialized['analysis_type'] = self.analysis_type
        serialized['subjects'] = {}
        for subject_id, subject in six.iteritems(self.subjects):
            serialized['subjects'][subject_id] = \
                subject.serialize(self.output_directory)
        serialized['parameters'] = {}
        for subject_id, analysis in six.iteritems(self.analyses):
            serialized['parameters'][subject_id] \
                = Study.serialize_paths(analysis.parameters,
                                        self.output_directory)
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
        s = 'label: ' + str(self.label) + '\n'
        s += 'output_directory: ' + str(self.output_directory) + '\n'
        s += 'subjects: ' + repr(self.subjects) + '\n'
        return s

    def get_subjects_from_pattern(self, exact_match=False,
                                  progress_callback=None):
        if progress_callback is not None:
            if isinstance(progress_callback, tuple):
                progress_callback, init_progress, scl_progess \
                    = progress_callback
            else:
                init_progress = 0.
                scl_progess = 1.
        subjects = []
        MODALITY = 't1mri'
        ACQUISITION = 'default_acquisition'
        any_dir = "([^/\\\\]+)"
        re_sep = os.sep.replace('\\', '\\\\')
        if progress_callback:
            progress_callback(init_progress)
        if exact_match:
            glob_pattern = os.path.join(
                self.output_directory, "*", "*", MODALITY, ACQUISITION,
                "*.nii")
            regexp = re.compile(
                             "^" + self.output_directory.replace('\\', '\\\\')
                                 + re_sep
                                 + any_dir + re_sep + any_dir + re_sep
                                 + MODALITY + re_sep + ACQUISITION + re_sep
                                 + "\\2\.(nii)$")

        else:
            glob_pattern = os.path.join(
                self.output_directory, "*", "*", MODALITY, "*", "*.*")
            regexp = re.compile(
                             "^" + self.output_directory.replace('\\', '\\\\')
                                 + re_sep
                                 + any_dir + re_sep + any_dir + re_sep
                                 + MODALITY + re_sep + any_dir + re_sep
                                 + "\\2\.((?:nii(?:\.gz)?)|(?:ima))$")

        vol_format = None
        ext_dict = {}  # TODO get if from capsul when it handles formats...
        # fix ambiguities in formats/ext dict
        ext_dict.update({
            "nii.gz": "NIFTI gz",
            "nii": "NIFTI",
            "ima": "GIS",
            "mnc": "MINC",
            "gii": "GIFTI",
            "mesh": "MESH",
            "ply": "PLY",
        })
        subjects_ids = set()
        files_list = list(glob.iglob(glob_pattern))
        nfiles = len(files_list)
        progress = 0.5
        for n, filename in enumerate(files_list):
            if progress_callback:
                progress_callback(
                    init_progress
                    + (progress + (1. - progress) * n / nfiles) * scl_progess)
            match = regexp.match(filename)
            if match:
                groupname = match.group(1)
                subjectname = match.group(2)
                if exact_match:
                    format_ext = match.group(3)
                else:
                    format_ext = match.group(4)
                format_name = ext_dict.get(format_ext, 'NIFTI gz')
                if vol_format is None:
                    vol_format = format_name
                    self.volumes_format = vol_format
                elif vol_format != format_name:
                    print('Warning: subject %s input MRI does not have '
                          'the expected format: %s, expecting %s'
                          % (subjectname, format_name, vol_format))
                    continue # skip this subject
                subject = Subject(subjectname, groupname, filename)
                subject_id = subject.id()
                if subject_id in subjects_ids:
                    print('Warning: %s / %s exists several times (in '
                          'different acquisitions probably) - keeping only '
                          'one.' % (subjectname, groupname))
                    continue
                subjects_ids.add(subject_id)
                subjects.append(subject)

        if progress_callback:
            progress_callback(init_progress + scl_progess)
        return subjects

    @classmethod
    def serialize_paths(cls, params, directory):
        new_params = {}
        items = [(params, new_params)]
        while items:
            item, parent = items.pop(0)
            if hasattr(item, 'items'):
                for name, sub_item in six.iteritems(item):
                    if hasattr(sub_item, 'keys') \
                            or isinstance(sub_item, (list, set)):
                        if isinstance(sub_item, (list, set)):
                            parent[name] = []
                        else:
                            parent[name] = sub_item.__class__()
                        items.append((sub_item, parent[name]))
                    elif isinstance(sub_item, six.string_types) \
                            and sub_item.startswith(directory):
                        parent[name] = os.path.join(
                            '${output_directory}',
                            os.path.relpath(sub_item, directory))
                    elif sub_item == undefined:
                        #parent[name] = '<undefined>'
                        pass
                    else:
                        parent[name] = sub_item
            elif isinstance(item, (list, set)):
                for sub_item in item:
                    if hasattr(sub_item, 'keys') \
                            or isinstance(sub_item, (list, set)):
                        if isinstance(sub_item, (list, set)):
                            parent.append([])
                        else:
                            parent.append(sub_item.__class__())
                        items.append((sub_item, parent[-1]))
                    elif isinstance(sub_item, six.string_types) \
                            and sub_item.startswith(directory):
                        parent.append(os.path.join(
                            '${output_directory}',
                            os.path.relpath(sub_item, directory)))
                    elif sub_item == undefined:
                        #parent.append('<undefined>')
                        pass
                    else:
                        parent.append(sub_item)
        return new_params

    @classmethod
    def unserialize_paths(cls, params, directory):
        new_params = {}
        items = [(params, new_params)]
        while items:
            item, parent = items.pop(0)
            if hasattr(item, 'items'):
                for name, sub_item in six.iteritems(item):
                    if hasattr(sub_item, 'keys') \
                            or isinstance(sub_item, list):
                        parent[name] = sub_item.__class__()
                        items.append((sub_item, parent[name]))
                    elif isinstance(sub_item, six.string_types) \
                            and sub_item.startswith('${output_directory}'):
                        parent[name] = sub_item.replace(
                            '${output_directory}', directory)
                    elif sub_item == '<undefined>':
                        parent[name] = undefined
                    else:
                        parent[name] = sub_item
            elif isinstance(item, list):
                for sub_item in item:
                    if hasattr(sub_item, 'keys') \
                            or isinstance(sub_item, list):
                        parent.append(sub_item.__class__())
                        items.append((sub_item, parent[-1]))
                    elif isinstance(sub_item, six.string_types) \
                            and sub_item.startswith(directory):
                        parent.append(sub_item.replace(
                            '${output_directory}', directory))
                    elif sub_item == '<undefined>':
                        parent.append(undefined)
                    else:
                        parent.append(sub_item)
        return new_params

    def convert_from_formats(self, old_volumes_format, old_meshes_format,
                             progress_callback=None):
        if progress_callback:
            if isinstance(progress_callback, tuple):
                callback, progr_init, progr_scl = progress_callback
            else:
                callback = progress_callback
                progr_init = 0.
                progr_scl = 1.
                progress_callback = (callback, progr_init, progr_scl)
        ns = len(self.subjects)
        if progress_callback:
            callback(progr_init)
        for n, subject_id in enumerate(self.subjects):
            print('convert', subject_id)
            self.analyses[subject_id].convert_from_formats(
                old_volumes_format, old_meshes_format)
            if progress_callback:
                callback(progr_init + (n + 1) * progr_scl / ns)


class StudySerializationError(Exception):
    pass

class SubjectExistsError(Exception):
    pass
