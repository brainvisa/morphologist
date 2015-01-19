from optparse import OptionParser
import os
import tempfile
import shutil


RIGHT = 'right'
LEFT = 'left'


class SulciError(Exception):
    pass


class Sulci(object):
         
    @staticmethod
    def run(mri_corrected, 
            split_mask, 
            grey, 
            talairach_transformation, 
            grey_white, 
            commissure_coordinates,
            white_surface,
            grey_surface,
            sulci,
            side,
            fix_random_seed=True):

        ext = os.path.splitext(grey)[1]

        braing = tempfile.NamedTemporaryFile(suffix=ext)
        skeleton = tempfile.NamedTemporaryFile(suffix=ext)
        roots = tempfile.NamedTemporaryFile(suffix=ext)
        graphd = tempfile.mkdtemp()

        if side == LEFT:
            masklabel = '2'
        elif side == RIGHT:
            masklabel = '1'
        else:
            raise SulciError("Side must be %s or %s." %(LEFT, RIGHT))
 
        command = ['VipMask', '-i', mri_corrected, '-m', split_mask, 
                   '-o', braing.name, '-w', 't', '-l', masklabel]
        Sulci._run_command(command)

        command = ['VipSkeleton', '-i', grey, '-so', skeleton.name, '-vo',
                   roots.name, '-g', braing.name, '-w', 't', '-version', '2']
        if fix_random_seed:
            command.extend(['-srand', '10'])
        Sulci._run_command(command)

        graph = os.path.join(graphd, 'foldgraph')
        command = ['VipFoldArg', '-i', skeleton.name, '-v',
                   roots.name, '-o', graph, '-w', 'g'] 
        Sulci._run_command(command)

        command = ['AimsFoldArgAtt', '-i', skeleton.name, '-g', graph + '.arg', '-o', sulci,
                   '-m', talairach_transformation, '--graphversion', '3.1', 
                   '--apc', commissure_coordinates]
        Sulci._run_command(command)

        Sulci._close_and_remove(braing)
        Sulci._close_and_remove(skeleton)
        Sulci._close_and_remove(roots)
        shutil.rmtree(graphd)

        ext = os.path.splitext(grey)[1]
        sulci_voronoi = tempfile.NamedTemporaryFile(suffix=ext)
        command = ['AimsSulciVoronoi.py', '-f', sulci, '-g', 
                   grey, '-o', sulci_voronoi.name] 
        Sulci._run_command(command)

        command = ['AimsFoldsGraphThickness.py',
                   '-i', sulci, '-c', grey, '-g', grey_white, '-w', white_surface, 
                   '-l', grey_surface, '-o', sulci, '-v', sulci_voronoi.name ]
        Sulci._run_command(command)

        Sulci._close_and_remove(sulci_voronoi)


  
    @staticmethod 
    def _close_and_remove(tmpfile):
        tmpfile.close()
        if os.path.isfile(tmpfile.name):
            os.remove(tmpfile.name)


    @staticmethod
    def _run_command(command):
        str_command = ""
        for command_element in command:
            str_command = str_command + " '%s'" % command_element
        return_value = os.system(str_command)
        if return_value != 0:
            msg = "The following command failed : %s" % str_command
            raise SulciError(msg)

 
if __name__ == '__main__':
    parser = OptionParser(usage='%prog mri_corrected split_mask grey talairach_transformation grey_white commissure_coordinates white_surface grey_surface sulci side')
    options, args = parser.parse_args()
    if len(args) != 10:
        parser.error('Invalid arguments: all arguments are mandatory.')
    sulci_step = Sulci()
    corrected_mri, split_mask, grey, talairach_transformation, grey_white, commissure_coordinates, white_surface, grey_surface, sulci, side = args
    sulci_step.run(corrected_mri, split_mask, grey, talairach_transformation, grey_white, 
                   commissure_coordinates, white_surface, grey_surface, sulci, side)
