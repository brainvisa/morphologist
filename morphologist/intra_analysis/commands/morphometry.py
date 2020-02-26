from __future__ import absolute_import
import os
import glob
from optparse import OptionParser

from brainvisa.configuration import neuroConfig


RIGHT = 'right'
LEFT = 'left'


class MorphometryError(Exception):
    pass


class Morphometry(object):
    
    @classmethod
    def run(cls, labeled_sulci, side, normalized, csv):
        # XXX: we need to know how the output is named
        prefix = os.path.splitext(csv)[0]
        model = cls._find_model(side, normalized)
        command = ['siMorpho',
                   '-m', model,
                   '-g', labeled_sulci,
                   '-o', prefix,
                   '--label_attribute', 'label',
                   '--print-labels', '1',
                   '--name-descriptors', '1',
                   '--filter-attributes', 'label',
                   '--one-file', '1']
        cls._run_command(command)

    @staticmethod
    def _find_model(side, normalized):
        brainvisa_share_dir = neuroConfig.dataPath[0].directory
        models_relpath = 'models/models_2008/discriminative_models/3.1/'
        if side == LEFT:
            side_prefix = 'L'
        else:
            side_prefix = 'R'
        if normalized:
            model_name = 'folds_noroots_fd4_2009'
        else:
            model_name = 'folds_noroots_fd4_native_2010'
        model_dir = os.path.join(brainvisa_share_dir,
                models_relpath, side_prefix + model_name) 
        model_filepath = glob.glob(os.path.join(model_dir, '*.arg'))[0]
        return model_filepath

    @staticmethod
    def _run_command(command):
        str_command = ""
        for command_element in command:
            str_command = str_command + " '%s'" % command_element
        return_value = os.system(str_command)
        if return_value != 0:
            msg = "The following command failed : %s" % str_command
            raise MorphometryError(msg)


if __name__ == '__main__':
    parser = OptionParser(usage='%prog [--normalized] sulci_labelling side csv')
    parser.add_option('--normalized', dest='normalized',
        action='store_true', default=False,
        help='descriptors are standardized in a normalized space')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Invalid arguments: all arguments are mandatory.')
    morphometry_step = Morphometry()
    labeled_sulci, side, csv = args
    morphometry_step.run(labeled_sulci, side, options.normalized, csv)
