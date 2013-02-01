from optparse import OptionParser
import os
import tempfile

from morphologist.intra_analysis_surface import Surface

RIGHT = 'right'
LEFT = 'left'

class GreySurfaceError(Exception):
    pass

class GreySurface(object):
         
    @staticmethod
    def run(mri_corrected, split_mask, grey, grey_surface, side, fix_random_seed=True):
        # temporary files must be in GIS format to reproduce Brainvisa process results 
        # (Brainvisa processes use GIS format temporary files)
        #ext = os.path.splitext(grey)[1]
        ext = '.ima'
        braing = tempfile.NamedTemporaryFile(suffix=ext)
        skeleton = tempfile.NamedTemporaryFile(suffix=ext)
        roots = tempfile.NamedTemporaryFile(suffix=ext)
        hemi = tempfile.NamedTemporaryFile(suffix=ext)
 
        if side == LEFT:
            masklabel = '2'
        elif side == RIGHT:
            masklabel = '1'
        else:
            raise GreySurfaceError("Side must be %s or %s." %(LEFT, RIGHT))

        command = ['VipMask', '-i', mri_corrected, '-m', split_mask, '-o', braing.name,
                   '-w', 't', '-l', masklabel ]
        GreySurface._run_command(command)

        command = ['VipSkeleton', '-i', grey, '-so', skeleton.name, 
                   '-vo', roots.name, '-g', braing.name, '-w', 't' ]
        if fix_random_seed:
            command.extend(['-srand', '10'])
        GreySurface._run_command(command)
 
        command = ['VipHomotopic', '-i', braing.name, '-s', skeleton.name, 
                   '-co', grey, '-o', hemi.name, '-m', 'H', '-w', 't']
        if fix_random_seed:
            command.extend(['-srand', '10'])
        GreySurface._run_command(command)

        Surface.run(hemi.name, grey_surface)

        skeleton.close()
        roots.close()
        braing.close() 
        hemi.close()


    @staticmethod
    def _run_command(command):
        str_command = ""
        for command_element in command:
            str_command = str_command + " '%s'" % command_element
        return_value = os.system(str_command)
        if return_value != 0:
            msg = "The following command failed : %s" % str_command
            raise GreySurfaceError(msg)

 
if __name__ == '__main__':
    parser = OptionParser(usage='%prog mri_corrected split_mask grey grey_surface side')
    options, args = parser.parse_args()
    if len(args) != 5:
        parser.error('Invalid arguments: all arguments are mandatory.')
    grey_surface_step = GreySurface()
    corrected_mri, split_mask, grey, grey_surface, side = args
    grey_surface_step.run(corrected_mri, split_mask, grey, grey_surface, side)
