from optparse import OptionParser
import os
import tempfile
import shutil

from brainvisa.configuration import neuroConfig

RIGHT = 'right'
LEFT = 'left'

class SulciLabellingError(Exception):
    pass

class SulciLabelling(object):
         
    @staticmethod
    def run(sulci,
            labeled_sulci,
            side,
            fix_random_seed=True):

        brainvisa_share_directory = neuroConfig.dataPath[0].directory
        model_2008_dir_name = os.path.join(brainvisa_share_directory, 'models', 'models_2008') 
        labels_translation_map = os.path.join(brainvisa_share_directory, 'nomenclature',
                                              'translation', 'sulci_model_2008.trl') 

        if side == LEFT:
            labels_priors_dir_name = 'frequency_segments_priors_left'
            global_registered_spam = 'global_registered_spam_left'
            locally_from_global_spam = 'locally_from_global_registred_spam_left'
        elif side == RIGHT:
            labels_priors_dir_name = 'frequency_segments_priors_right'
            global_registered_spam = 'global_registered_spam_right'
            locally_from_global_spam = 'locally_from_global_registred_spam_right'
        else:
            raise SulciLabellingError("Side must be %s or %s." %(LEFT, RIGHT))
            
        labels_priors = os.path.join(model_2008_dir_name, 'descriptive_models', 'labels_priors', 
                                     labels_priors_dir_name, 'frequency_segments_priors.dat')
        translation_priors = os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    locally_from_global_spam, 'gaussian_translation_trm_priors.dat')
        direction_priors = os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    locally_from_global_spam, 'bingham_direction_trm_priors.dat')
        angle_priors = os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    locally_from_global_spam, 'vonmises_angle_trm_priors.dat') 
        local_referencials =  os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    locally_from_global_spam, 'local_referentials.dat') 
        model_global = os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    global_registered_spam, 'spam_distribs.dat')
        model_local = os.path.join(model_2008_dir_name, 'descriptive_models', 'segments', 
                                    locally_from_global_spam, 'spam_distribs.dat')


        posterior_probabilities_global = tempfile.NamedTemporaryFile(suffix='.csv')
        posterior_probabilities_local = tempfile.NamedTemporaryFile(suffix='.csv')
        tmpfile_local = tempfile.NamedTemporaryFile(suffix='.txt')
        tmpfile_global = tempfile.NamedTemporaryFile(suffix='.txt')
        tal_to_spam_transformation = tempfile.NamedTemporaryFile(suffix='.trm')
        transformation_matrix = tempfile.NamedTemporaryFile(suffix='.trm')
        t1_to_global_transformation = tempfile.NamedTemporaryFile(suffix='.trm')
        global_to_local_transformation = tempfile.mkdtemp()

        indep_tag_with_reg_command_path = os.path.join(neuroConfig.basePath, 'scripts', 
                                                       'sigraph', 'sulci_registration', 
                                                       'independent_tag_with_registration.py')

        command = [indep_tag_with_reg_command_path, '-i', sulci, '-o',
                   labeled_sulci, '-t', labels_translation_map, '-d', model_global,
                   '-c', posterior_probabilities_local.name, '-l', tmpfile_local.name,
                   '-p', labels_priors, '--mode', 'global', '--motion',
                   tal_to_spam_transformation.name]
        SulciLabelling._run_command(command)

        command = ['AimsGraphExtractTransformation', '-i', sulci,
                   '-o', transformation_matrix.name]  
        SulciLabelling._run_command(command)
        
        command = ['AimsComposeTransformation', '-i', tal_to_spam_transformation.name, 
                   '-j', transformation_matrix.name,
                   '-o', t1_to_global_transformation.name]  
        SulciLabelling._run_command(command)

        command = [indep_tag_with_reg_command_path, '-i', labeled_sulci, 
                   '-o', labeled_sulci, '-t', labels_translation_map,
                   '-d', model_local, '-c', posterior_probabilities_global.name, 
                   '-l', tmpfile_global.name, '-p', labels_priors, 
                   '--translation-prior', translation_priors, 
                   '--direction-prior', direction_priors,
                   '--angle-prior', angle_priors, 
                   '--distrib-gaussians', local_referencials, 
                   '--mode', 'local',
                   '--input-motion', tal_to_spam_transformation.name,
                   '--motion', global_to_local_transformation]
        SulciLabelling._run_command(command)
 
        posterior_probabilities_local.close()
        tmpfile_local.close()
        tmpfile_global.close()
        tal_to_spam_transformation.close()
        t1_to_global_transformation.close()
        transformation_matrix.close()
        shutil.rmtree(global_to_local_transformation)


    @staticmethod
    def _run_command(command):
        str_command = ""
        for command_element in command:
            str_command = str_command + " '%s'" % command_element
        return_value = os.system(str_command)
        if return_value != 0:
            msg = "The following command failed : %s" % str_command
            raise SulciLabellingError(msg)

 
if __name__ == '__main__':
    parser = OptionParser(usage='%prog mri_corrected split_mask grey talairach_transformation grey_white')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Invalid arguments: all arguments are mandatory.')
    sulci_labelling_step = SulciLabelling()
    sulci, labeled_sulci, side = args    
    sulci_labelling_step.run(sulci, labeled_sulci, side) 

