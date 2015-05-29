import os
import shutil
import re
import glob

from morphologist.core.analysis import Parameters, ParameterTemplate
from morphologist.core.utils import create_directory_if_missing, create_directories_if_missing
from morphologist.core.subject import Subject


class IntraAnalysisParameterNames:
    # intra analysis parameters (inputs / outputs)
    MRI = 'mri'
    MRI_REFERENTIAL = 'mri_referential'
    COMMISSURE_COORDINATES = 'commissure_coordinates'
    TALAIRACH_TRANSFORMATION = 'talairach_transformation'
    EROSION_SIZE = 'erosion_size' 
    BARY_FACTOR = 'bary_factor'
    HFILTERED = 'hfiltered'
    WHITE_RIDGES = 'white_ridges'
    EDGES = 'edges'
    VARIANCE = 'variance'
    CORRECTED_MRI = 'corrected_mri'
    HISTO_ANALYSIS = 'histo_analysis'
    HISTOGRAM = 'histogram'
    BRAIN_MASK = 'brain_mask'
    SPLIT_MASK = 'split_mask'
    LEFT_GREY_WHITE = 'left_grey_white'
    RIGHT_GREY_WHITE = 'right_grey_white'
    LEFT_GREY = 'left_grey'
    RIGHT_GREY = 'right_grey'
    LEFT_GREY_SURFACE = 'left_grey_surface'
    RIGHT_GREY_SURFACE = 'right_grey_surface'
    LEFT_WHITE_SURFACE = 'left_white_surface'
    RIGHT_WHITE_SURFACE = 'right_white_surface'
    LEFT_SULCI = 'left_sulci'
    RIGHT_SULCI = 'right_sulci'
    LEFT_LABELED_SULCI = 'left_labeled_sulci'
    RIGHT_LABELED_SULCI = 'right_labeled_sulci'
    # XXX _DATA are used to hardcode .data directory generated with .arg files
    LEFT_SULCI_DATA = 'left_sulci_data'
    RIGHT_SULCI_DATA = 'right_sulci_data'
    LEFT_LABELED_SULCI_DATA = 'left_labeled_sulci_data'
    RIGHT_LABELED_SULCI_DATA = 'right_labeled_sulci_data'
    LEFT_NATIVE_MORPHOMETRY_CSV = 'left_native_morphometry'
    RIGHT_NATIVE_MORPHOMETRY_CSV = 'right_native_morphometry'
    LEFT_NORMALIZED_MORPHOMETRY_CSV = 'left_normalized_morphometry'
    RIGHT_NORMALIZED_MORPHOMETRY_CSV = 'right_normalized_morphometry'

    @classmethod
    def get_input_file_parameter_names(cls):
        return [cls.MRI, cls.MRI_REFERENTIAL]

    @classmethod
    def get_input_other_parameter_names(cls):
        return [cls.EROSION_SIZE, cls.BARY_FACTOR]

    @classmethod
    def get_output_file_parameter_names(cls):
        return [cls.COMMISSURE_COORDINATES,
                cls.TALAIRACH_TRANSFORMATION,
                cls.HFILTERED,
                cls.WHITE_RIDGES,
                cls.EDGES,
                cls.VARIANCE,
                cls.CORRECTED_MRI,
                cls.HISTO_ANALYSIS,
                cls.HISTOGRAM,
                cls.BRAIN_MASK,
                cls.SPLIT_MASK,
                cls.LEFT_GREY_WHITE,
                cls.RIGHT_GREY_WHITE,
                cls.LEFT_GREY,
                cls.RIGHT_GREY,
                cls.LEFT_GREY_SURFACE,
                cls.RIGHT_GREY_SURFACE,
                cls.LEFT_WHITE_SURFACE,
                cls.RIGHT_WHITE_SURFACE,
                cls.LEFT_SULCI,
                cls.RIGHT_SULCI,
                cls.LEFT_SULCI_DATA,
                cls.RIGHT_SULCI_DATA,
                cls.LEFT_LABELED_SULCI,
                cls.RIGHT_LABELED_SULCI,
                cls.LEFT_LABELED_SULCI_DATA,
                cls.RIGHT_LABELED_SULCI_DATA,
                cls.LEFT_NATIVE_MORPHOMETRY_CSV,
                cls.RIGHT_NATIVE_MORPHOMETRY_CSV,
                cls.LEFT_NORMALIZED_MORPHOMETRY_CSV,
                cls.RIGHT_NORMALIZED_MORPHOMETRY_CSV,
                ]


class IntraAnalysisParameterTemplate(ParameterTemplate):
    input_file_param_names = \
        IntraAnalysisParameterNames.get_input_file_parameter_names()
    input_other_param_names = \
        IntraAnalysisParameterNames.get_input_other_parameter_names()
    output_file_param_names = \
        IntraAnalysisParameterNames.get_output_file_parameter_names()

    @classmethod
    def get_empty_inputs(cls):
        return IntraAnalysisParameters(cls.input_file_param_names,
                               cls.input_other_param_names)

    @classmethod
    def get_empty_outputs(cls):
        return IntraAnalysisParameters(cls.output_file_param_names)

    def get_inputs(self, subject):
        self.create_fom_completion(subject)
        analysis = self.study.analyses[subject.id()]
        pipeline = analysis.pipeline
        mp = pipeline.process

        parameters = IntraAnalysisParameters(self.input_file_param_names,
                                     self.input_other_param_names)
        parameters[IntraAnalysisParameterNames.MRI] = mp.t1mri
        parameters[IntraAnalysisParameterNames.MRI_REFERENTIAL] \
            = mp.PrepareSubject_TalairachFromNormalization_source_referential
        parameters[IntraAnalysisParameterNames.EROSION_SIZE] = 1.8
        parameters[IntraAnalysisParameterNames.BARY_FACTOR] = 0.6
        return parameters

    def create_fom_completion(self, subject):
        analysis = self.study.analyses[subject.id()]
        pipeline = analysis.pipeline
        attributes_dict = {
            'center': subject.groupname,
            'subject': subject.name,
            'acquisition': self.ACQUISITION,
            'analysis': self.ANALYSIS,
            'graph_version': self.GRAPH_VERSION,
            'sulci_recognition_session': self.FOLDS_SESSION
        }
        do_completion = False
        for attribute, value in attributes_dict.iteritems():
            if pipeline.attributes[attribute] != value:
                pipeline.attributes[attribute] = value
                do_completion = True
        if do_completion:
            print 'create_completion for:', subject.id()
            pipeline.create_completion()
        else: print 'skip completion for:', subject.id()



class BrainvisaIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):
    name = "brainvisa"
    ACQUISITION = "default_acquisition"
    ANALYSIS = "default_analysis"
    REGISTRATION = "registration"
    MODALITY = "t1mri"
    SEGMENTATION = "segmentation"
    SURFACE = "mesh"
    FOLDS = os.path.join("folds", "3.1")
    GRAPH_VERSION = "3.1"
    SESSION_AUTO = "default_session_auto"
    FOLDS_SESSION = "default_session"

    def get_subject_filename(self, subject):
        format = self.study.volumes_format or "NIFTI"
        ext = self.study.modules_data.foms["input"].formats[format]
        return os.path.join(
            self._base_directory, subject.groupname, subject.name,
            self.MODALITY, self.ACQUISITION, subject.name + "." + ext)

    def get_outputs(self, subject):
        self.create_fom_completion(subject)
        analysis = self.study.analyses[subject.id()]
        pipeline = analysis.pipeline
        mp = pipeline.process

        parameters = IntraAnalysisParameters(self.output_file_param_names)

        parameters[IntraAnalysisParameterNames.COMMISSURE_COORDINATES] \
            = mp.commissure_coordinates
        parameters[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION] \
            = mp.Talairach_transform
        parameters[IntraAnalysisParameterNames.HFILTERED] \
            = mp.BiasCorrection_hfiltered
        parameters[IntraAnalysisParameterNames.WHITE_RIDGES] \
            = mp.BiasCorrection_white_ridges
        parameters[IntraAnalysisParameterNames.EDGES] \
            = mp.BiasCorrection_edges
        parameters[IntraAnalysisParameterNames.CORRECTED_MRI] = mp.t1mri_nobias
        parameters[IntraAnalysisParameterNames.VARIANCE] \
            = mp.BiasCorrection_variance
        parameters[IntraAnalysisParameterNames.HISTO_ANALYSIS] \
            = mp.histo_analysis
        parameters[IntraAnalysisParameterNames.HISTOGRAM] \
            = mp.HistoAnalysis_histo
        parameters[IntraAnalysisParameterNames.BRAIN_MASK] \
            = mp.BrainSegmentation_brain_mask
        parameters[IntraAnalysisParameterNames.SPLIT_MASK] = mp.split_brain
        parameters[IntraAnalysisParameterNames.LEFT_GREY_WHITE] \
            = mp.GreyWhiteClassification_grey_white
        parameters[IntraAnalysisParameterNames.RIGHT_GREY_WHITE] \
            = mp.GreyWhiteClassification_1_grey_white
        parameters[IntraAnalysisParameterNames.LEFT_GREY] \
            = mp.GreyWhiteTopology_hemi_cortex
        parameters[IntraAnalysisParameterNames.RIGHT_GREY] \
            = mp.GreyWhiteTopology_1_hemi_cortex
        parameters[IntraAnalysisParameterNames.LEFT_GREY_SURFACE] \
            = mp.PialMesh_pial_mesh
        parameters[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE] \
            = mp.PialMesh_1_pial_mesh
        parameters[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE] \
            = mp.GreyWhiteMesh_white_mesh
        parameters[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE] \
            = mp.GreyWhiteMesh_1_white_mesh
        parameters[IntraAnalysisParameterNames.LEFT_SULCI] \
            = mp.left_graph
        parameters[IntraAnalysisParameterNames.RIGHT_SULCI] \
            = mp.right_graph
        parameters[IntraAnalysisParameterNames.LEFT_SULCI_DATA] \
            = mp.left_graph[:mp.left_graph.rfind('.')] + ".data"
        parameters[IntraAnalysisParameterNames.RIGHT_SULCI_DATA] \
            = mp.right_graph[:mp.right_graph.rfind('.')] + ".data"
        parameters[IntraAnalysisParameterNames.LEFT_LABELED_SULCI] \
            = mp.left_labelled_graph
        parameters[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI] \
            = mp.right_labelled_graph
        parameters[IntraAnalysisParameterNames.LEFT_LABELED_SULCI_DATA] \
            = mp.left_labelled_graph[:mp.left_labelled_graph.rfind('.')] \
                + ".data"
        parameters[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI_DATA] \
            = mp.right_labelled_graph[:mp.right_labelled_graph.rfind('.')] \
                + ".data"

        # TODO: use FOM for morphometry
        session_auto_path = os.path.dirname(mp.left_labelled_graph)
        parameters[IntraAnalysisParameterNames.LEFT_NATIVE_MORPHOMETRY_CSV] = \
            os.path.join(session_auto_path,
                         'left_native_morphometry_%s.dat' % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_NATIVE_MORPHOMETRY_CSV] = \
            os.path.join(session_auto_path,
                         'right_native_morphometry_%s.dat' % subject.name)
        parameters[
            IntraAnalysisParameterNames.LEFT_NORMALIZED_MORPHOMETRY_CSV] = \
                os.path.join(session_auto_path,
                             'left_normalized_morphometry_%s.dat'
                             % subject.name)
        parameters[
            IntraAnalysisParameterNames.RIGHT_NORMALIZED_MORPHOMETRY_CSV] = \
                os.path.join(session_auto_path,
                             'right_normalized_morphometry_%s.dat'
                             % subject.name)
        return parameters

    def create_outputdirs(self, subject):
        group_path = os.path.join(self._base_directory, subject.groupname)
        create_directory_if_missing(group_path)

        subject_path = os.path.join(group_path, subject.name)
        create_directory_if_missing(subject_path)

        t1mri_path = os.path.join(subject_path, self.MODALITY)
        create_directory_if_missing(t1mri_path)

        default_acquisition_path = os.path.join(t1mri_path, self.ACQUISITION)
        create_directory_if_missing(default_acquisition_path)

        registration_path = os.path.join(
            default_acquisition_path, self.REGISTRATION)
        create_directory_if_missing(registration_path)

        default_analysis_path = os.path.join(
            default_acquisition_path, self.ANALYSIS)
        create_directory_if_missing(default_analysis_path)

        segmentation_path = os.path.join(
            default_analysis_path, self.SEGMENTATION)
        create_directory_if_missing(segmentation_path)

        surface_path = os.path.join(segmentation_path, self.SURFACE)
        create_directory_if_missing(surface_path)

        folds_path = os.path.join(default_analysis_path, self.FOLDS)
        create_directories_if_missing(folds_path)

        session_auto_path = os.path.join(folds_path, self.SESSION_AUTO)
        create_directory_if_missing(session_auto_path)

    def remove_dirs(self, subject):
        group_path = os.path.join(self._base_directory, subject.groupname)
        subject_path = os.path.join(group_path, subject.name)
        shutil.rmtree(subject_path)

    def get_subjects(self, exact_match=False):
        subjects = []
        any_dir = "([^/]+)"
        if exact_match:
            glob_pattern = os.path.join(
                self._base_directory, "*", "*", self.MODALITY, self.ACQUISITION,
                "*.nii")
            regexp = re.compile(
                "^"+os.path.join(self._base_directory, any_dir, any_dir,
                                 self.MODALITY, self.ACQUISITION,
                                 "\\2\.(?:nii)$"))

        else:
            glob_pattern = os.path.join(
                self._base_directory, "*", "*", self.MODALITY, "*", "*.*")
            regexp = re.compile(
                "^" + os.path.join(
                    self._base_directory, any_dir, any_dir, self.MODALITY,
                    any_dir, "\\2\.(?:(?:nii(?:\.gz)?)|(?:ima))$"))
        for filename in glob.iglob(glob_pattern):
            match = regexp.match(filename)
            if match:
                groupname = match.group(1)
                subjectname = match.group(2)
                subject = Subject(subjectname, groupname, filename)
                subjects.append(subject)
        return subjects


class DefaultIntraAnalysisParameterTemplate(IntraAnalysisParameterTemplate):
    name = "default"

    def get_subject_filename(self, subject):
        return os.path.join(self._base_directory, subject.groupname, subject.name, 
                            subject.name + ".nii")

    def get_outputs(self, subject):
        parameters = IntraAnalysisParameters(self.output_file_param_names)

        subject_path = os.path.join(self._base_directory, subject.groupname, subject.name)
        parameters[IntraAnalysisParameterNames.COMMISSURE_COORDINATES] = os.path.join(subject_path, 
                                                         "%s.APC" %subject.name)
        parameters[IntraAnalysisParameterNames.TALAIRACH_TRANSFORMATION] = os.path.join(subject_path,
                                                            "RawT1-%s_TO_Talairach-ACPC.trm" 
                                                            % subject.name)
        parameters[IntraAnalysisParameterNames.HFILTERED] = os.path.join(subject_path, 
                                            "hfiltered_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.WHITE_RIDGES] = os.path.join(subject_path, 
                                            "whiteridge_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.EDGES] = os.path.join(subject_path, 
                                            "edges_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.CORRECTED_MRI] = os.path.join(subject_path, 
                                            "nobias_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.VARIANCE] = os.path.join(subject_path, 
                                            "variance_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.HISTO_ANALYSIS] = os.path.join(subject_path, 
                                            "nobias_%s.han" % subject.name)
        parameters[IntraAnalysisParameterNames.HISTOGRAM] = os.path.join(subject_path, 
                                            "nobias_%s.his" % subject.name)
        parameters[IntraAnalysisParameterNames.BRAIN_MASK] = os.path.join(subject_path, 
                                            "brain_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.SPLIT_MASK] = os.path.join(subject_path, 
                                            "voronoi_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_GREY_WHITE] = os.path.join(\
                subject_path, "left_grey_white_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_GREY_WHITE] = os.path.join(\
                subject_path, "right_grey_white_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_GREY] = os.path.join(\
                subject_path, "left_grey_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_GREY] = os.path.join(\
                subject_path, "right_grey_%s.nii" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_GREY_SURFACE] = os.path.join(\
                subject_path, "left_grey_surface_%s.gii" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_GREY_SURFACE] = os.path.join(\
                subject_path, "right_grey_surface_%s.gii" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_WHITE_SURFACE] = os.path.join(\
                subject_path, "left_white_surface_%s.gii" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_WHITE_SURFACE] = os.path.join(\
                subject_path, "right_white_surface_%s.gii" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_SULCI] = os.path.join(\
                subject_path, "left_sulci_%s.arg" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_SULCI] = os.path.join(\
                subject_path, "right_sulci_%s.arg" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_SULCI_DATA] = os.path.join(\
                subject_path, "left_sulci_%s.data" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_SULCI_DATA] = os.path.join(\
                subject_path, "right_sulci_%s.data" % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_LABELED_SULCI] = os.path.join(\
                subject_path, "left_labeled_sulci_%s.arg" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI] = os.path.join(\
                subject_path, "right_labeled_sulci_%s.arg" % subject.name) 
        parameters[IntraAnalysisParameterNames.LEFT_LABELED_SULCI_DATA] = os.path.join(\
                subject_path, "left_labeled_sulci_%s.data" % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_LABELED_SULCI_DATA] = os.path.join(\
                subject_path, "right_labeled_sulci_%s.data" % subject.name) 

        parameters[IntraAnalysisParameterNames.LEFT_NATIVE_MORPHOMETRY_CSV] = \
            os.path.join(subject_path, 'left_native_morphometry_%s.dat' % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_NATIVE_MORPHOMETRY_CSV] = \
            os.path.join(subject_path, 'right_native_morphometry_%s.dat' % subject.name)
        parameters[IntraAnalysisParameterNames.LEFT_NORMALIZED_MORPHOMETRY_CSV] = \
            os.path.join(subject_path, 'left_normalized_morphometry_%s.dat' % subject.name)
        parameters[IntraAnalysisParameterNames.RIGHT_NORMALIZED_MORPHOMETRY_CSV] = \
            os.path.join(subject_path, 'right_normalized_morphometry_%s.dat' % subject.name)
        return parameters

    def create_outputdirs(self, subject):
        group_path = os.path.join(self._base_directory, subject.groupname)
        create_directory_if_missing(group_path)
        subject_path = os.path.join(group_path, subject.name)
        create_directory_if_missing(subject_path)    

    def remove_dirs(self, subject):
        group_path = os.path.join(self._base_directory, subject.groupname)
        subject_path = os.path.join(group_path, subject.name)
        shutil.rmtree(subject_path)

    def get_subjects(self, exact_match=False):
        subjects = []
        any_dir = "([^/]+)"
        if exact_match:
            glob_pattern = os.path.join(self._base_directory, "*", "*", "*.nii")
            regexp=re.compile(
                "^"+os.path.join(self._base_directory, any_dir, any_dir,
                                 "\\2\.(?:nii)$"))
        else:
            glob_pattern = os.path.join(self._base_directory, "*", "*", "*.*")
            regexp=re.compile(
                "^"+os.path.join(self._base_directory, any_dir, any_dir,
                                 "\\2\.(?:(?:nii(?:\.gz)?)|(?:ima))$"))
        for filename in glob.iglob(glob_pattern):
            match=regexp.match(filename)
            if match:
                groupname = match.group(1)
                subjectname = match.group(2)
                subject = Subject(subjectname, groupname, filename)
                subjects.append(subject)
        return subjects


class IntraAnalysisParameters(Parameters):
    
    @classmethod
    def _clear_file(cls, filename):
        super(IntraAnalysisParameters, cls)._clear_file(filename)
        minf_filename = filename + ".minf"
        if os.path.exists(minf_filename):
            os.remove(minf_filename)
