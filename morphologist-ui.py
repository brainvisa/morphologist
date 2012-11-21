import os, sys

from morphologist.study import Study
from morphologist.gui.qt_backend import QtGui, loadUi
from morphologist.gui import ManageStudyWindow, create_main_window

def main():
    qApp = QtGui.QApplication(sys.argv)
    main_window = create_main_window()
    main_window.ui.show()
    sys.exit(qApp.exec_())

if __name__ == '__main__' : main()
