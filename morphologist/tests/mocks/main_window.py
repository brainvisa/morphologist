from morphologist.gui.main_window import IntraAnalysisWindow
from morphologist.tests.mocks.study import MockStudy 

class MockIntraAnalysisWindow(IntraAnalysisWindow):

   def _create_study(self):
      #study = MockStudy.from_file("/tmp/my_study")
      ##study = MockStudy.from_file("/tmp/big_study")
      #study.clear_results()
      #return study
      return MockStudy()
 

def create_main_window():
    return MockIntraAnalysisWindow()

