from morphologist.gui.main_window import MainWindow


class MockMainWindow(MainWindow):
    
    def __init__(self, analysis_type, study_file=None):
        super(MockMainWindow, self).__init__(analysis_type="Mock"+analysis_type, 
                                             study_file=study_file)
        
    def _window_title(self):
        return "Morphologist - %s --- MOCK MODE ---" % self.study.name
