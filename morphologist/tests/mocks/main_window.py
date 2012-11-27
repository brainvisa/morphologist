from morphologist.gui.main_window import IntraAnalysisWindow
from morphologist.tests.mocks.study import MockStudy 

class MockIntraAnalysisWindow(IntraAnalysisWindow):

   def _create_study(self, study_file=None):
      if study_file:
          study = MockStudy.from_file(study_file)
          return study
      else:
          return MockStudy()



