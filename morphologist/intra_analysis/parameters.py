

class IntraAnalysisParameterNames:
    # intra analysis parameters (inputs / outputs)
    MRI = 't1mri'
    MRI_REFERENTIAL = 'PrepareSubject_TalairachFromNormalization_source_referential'
    COMMISSURE_COORDINATES = 'commissure_coordinates'
    TALAIRACH_TRANSFORMATION = 'Talairach_transform'
    EROSION_SIZE = 'erosion_size' 
    BARY_FACTOR = 'bary_factor'
    HFILTERED = 'BiasCorrection_hfiltered'
    WHITE_RIDGES = 'BiasCorrection_white_ridges'
    EDGES = 'BiasCorrection_edges'
    VARIANCE = 'BiasCorrection_variance'
    CORRECTED_MRI = 't1mri_nobias'
    HISTO_ANALYSIS = 'histo_analysis'
    HISTOGRAM = 'HistoAnalysis_histo'
    BRAIN_MASK = 'BrainSegmentation_brain_mask'
    SPLIT_MASK = 'split_brain'
    LEFT_GREY_WHITE = 'GreyWhiteClassification_grey_white'
    RIGHT_GREY_WHITE = 'GreyWhiteClassification_1_grey_white'
    LEFT_GREY = 'GreyWhiteTopology_hemi_cortex'
    RIGHT_GREY = 'GreyWhiteTopology_1_hemi_cortex'
    LEFT_GREY_SURFACE = 'PialMesh_pial_mesh'
    RIGHT_GREY_SURFACE = 'PialMesh_1_pial_mesh'
    LEFT_WHITE_SURFACE = 'GreyWhiteMesh_white_mesh'
    RIGHT_WHITE_SURFACE = 'GreyWhiteMesh_1_white_mesh'
    LEFT_SULCI = 'left_graph'
    RIGHT_SULCI = 'right_graph'
    LEFT_LABELED_SULCI = 'left_labelled_graph'
    RIGHT_LABELED_SULCI = 'right_labelled_graph'
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

