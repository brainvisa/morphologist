from morphologist.gui.main_window import MainWindow


class MockMainWindow(MainWindow):

    def _window_title(self):
        return "Morphologist - %s --- MOCK MODE ---" % self.study.name
