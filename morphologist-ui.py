#! /usr/bin/env python
import sys
import optparse

from morphologist.core.settings import settings
from morphologist.core.gui.qt_backend import QtGui
from morphologist.gui.main_window import MainWindow


def option_parser():
    parser = optparse.OptionParser()

    parser.add_option('-s', '--study', 
                      dest="study_directory", metavar="STUDY_DIRECTORY", default=None, 
                      help="Opens the interface with the study loaded.")
    parser.add_option('-i', '--import', 
                      dest="import_study_directory", metavar="IMPORT_STUDY_DIRECTORY", default=None, 
                      help="Opens the interface with a new study loaded, based on an imported brainvisa directory.")
    
    group_neurospin = optparse.OptionGroup(parser, "Neurospin specific options")
    parser.add_option_group(group_neurospin)
    group_neurospin.add_option('--brainomics', action='callback', 
                               callback=brainomics_option_callback,
                               dest='brainomics', default=False,
                               help="Images can be imported in a study from "
                               "Brainomics Cubicweb database")
    group_debug = optparse.OptionGroup(parser, "Debug options")
    parser.add_option_group(group_debug)
    group_debug.add_option('--mock', action="callback",
            callback=mock_option_callback, dest='mock', default=False,
            help="Test mode, runs mock intra analysis") 
   
    return parser


def mock_option_callback(self, option, value, parser):
    settings.commandline.mock = True


def brainomics_option_callback(self, option, value, parser):
    settings.commandline.brainomics = True


def main():
    parser = option_parser()
    options, args = parser.parse_args(sys.argv)
    if not settings.are_valid():
        print "Warning: unvalid settings!"
        print "         User settings will be ignored, switch to default. "
        print "         Try to remove it or fix it."
        settings.load_default()
    if options.study_directory is not None \
            and options.import_study_directory is not None:
      print "-i and -s options are incompatible."
      parser.print_help()
      sys.exit(1)

    qApp = QtGui.QApplication(sys.argv)
    if options.import_study_directory is not None:
        study_directory = options.import_study_directory
        import_study = True
    else:
        study_directory = options.study_directory
        import_study = False
    main_window = MainWindow(analysis_type="IntraAnalysis",
                            study_directory=study_directory,
                            import_study=import_study)
    main_window.show()
    sys.exit(qApp.exec_())


if __name__ == '__main__' : main()
