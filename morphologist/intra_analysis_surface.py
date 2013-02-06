from optparse import OptionParser
import os
import tempfile


class SurfaceError(Exception):
    pass

class Surface(object):
         
    @staticmethod
    def run(mask, surface):
        # temporary files must be in GIS format to reproduce Brainvisa process results 
        # (Brainvisa processes use GIS format temporary files)
        #ext = os.path.splitext(mask)[1]
        ext = '.ima'
        tmp_file = tempfile.NamedTemporaryFile(suffix=ext)
        command_list = ['VipSingleThreshold', '-i', "'%s'" % mask, 
                        '-o', "'%s'" % tmp_file.name,
                        '-t', '0', '-c', 'b', '-m', 'ne', '-w', 't']
        Surface._run_command_list(command_list)

        command_list = ['AimsMeshBrain', '-i', "'%s'" % tmp_file.name,
                        '-o', "'%s'" % surface, '--internalinterface']
        Surface._run_command_list(command_list)
        Surface._close_and_remove(tmp_file)

        command_list = ['meshCleaner', '-i', "'%s'" % surface,
                       '-o', "'%s'" % surface, '-maxCurv', '0.5']
        Surface._run_command_list(command_list)


    @staticmethod
    def _close_and_remove(tmpfile):
        tmpfile.close()
        if os.path.isfile(tmpfile.name):
            os.remove(tmpfile.name)


    @staticmethod
    def _run_command_list(command_list):
        command = " ".join(command_list)
        return_value = os.system(command)
        if return_value != 0:
            msg = "The following command failed : %s" % command
            raise SurfaceError(msg)

 
if __name__ == '__main__':
    parser = OptionParser(usage='%prog mask_input_file surface_output_file')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Invalid arguments: all arguments are mandatory.')
    surface_step = Surface()
    mask, surface = args
    surface_step.run(mask, surface)
