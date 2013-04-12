from morphologist.core.study import Study


class IntraAnalysisStudy(Study):

    def __init__(self, name="undefined study", 
                 outputdir=Study.default_outputdir, parameter_template=None):
        super(IntraAnalysisStudy, self).__init__(analysis_type="IntraAnalysis", 
                                                 name=name, outputdir=outputdir, 
                                                 parameter_template=parameter_template)

