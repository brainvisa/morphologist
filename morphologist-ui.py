import sys
from morphologist.gui.qt_backend import QtGui

def main():
    qApp = QtGui.QApplication(sys.argv)
    sys.exit(qApp.exec_())

if __name__ == '__main__' : main()
