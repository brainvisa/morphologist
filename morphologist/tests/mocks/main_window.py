from morphologist.gui.main_window import IntraAnalysisWindow
from morphologist.tests.mocks.study import MockIntraAnalysisStudy 

class MockIntraAnalysisWindow(IntraAnalysisWindow):

   def _create_study(self, study_file=None):
      if study_file:
          study = MockIntraAnalysisStudy.from_file(study_file)
          return study
      else:
          return MockIntraAnalysisStudy()



