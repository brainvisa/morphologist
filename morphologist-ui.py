import sys
import optparse

from morphologist.gui.qt_backend import QtGui
from morphologist.gui.main_window import create_main_window

def option_parser():
    parser = optparse.OptionParser()

    parser.add_option('-s', '--study', 
                      dest="study_file", metavar="STUDY_FILE", default=None, 
                      help="Opens the interface with the study loaded.")
    parser.add_option('--mock', action="store_true", 
                      dest='mock', default=False,
                      help="Test mode, runs mock intra analysis") 
   
    return parser


def main():
    parser = option_parser()
    options, args = parser.parse_args(sys.argv)

    qApp = QtGui.QApplication(sys.argv)
    main_window = create_main_window(options.study_file, options.mock)
    main_window.show()
    sys.exit(qApp.exec_())


if __name__ == '__main__' : main()
