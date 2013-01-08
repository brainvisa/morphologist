from optparse import OptionParser
import os
import tempfile


class WhiteSurfaceError(Exception):
    pass

class WhiteSurface(object):
         
    @staticmethod
    def run(grey, white_surface):
        ext = os.path.splitext(grey)[1]
        white = tempfile.NamedTemporaryFile(suffix=ext)
        command_list = ['VipSingleThreshold', '-i', grey, '-o', white.name,
                        '-t', '0', '-c', 'b', '-m', 'ne', '-w', 't']
        WhiteSurface._run_command_list(command_list)

        command_list = ['AimsMeshBrain', '-i', white.name,
                        '-o', white_surface, '--internalinterface']
        WhiteSurface._run_command_list(command_list)
        white.close()

        command_list = ['meshCleaner', '-i', white_surface,
                       '-o', white_surface, '-maxCurv', '0.5']
        WhiteSurface._run_command_list(command_list)

    @staticmethod
    def _run_command_list(command_list):
        command = " ".join(command_list)
        return_value = os.system(command)
        if return_value != 0:
            msg = "The following command failed : %s" % command
            raise WhiteSurfaceError(msg)

 
if __name__ == '__main__':
    parser = OptionParser(usage='%prog grey_input_file white_surface_output_file')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Invalid arguments: all arguments are mandatory.')
    white_surface_step = WhiteSurface()
    grey, white_surface = args
    white_surface_step.run(grey, white_surface)
