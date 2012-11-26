import sys

from morphologist.gui.qt_backend import QtGui
from morphologist.tests.mocks.main_window import create_main_window

def main():
    qApp = QtGui.QApplication(sys.argv)
    main_window = create_main_window()
    main_window.ui.show()
    sys.exit(qApp.exec_())

if __name__ == '__main__' : main()
