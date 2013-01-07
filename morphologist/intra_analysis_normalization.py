from optparse import OptionParser
import os
import uuid

import brainvisa.axon
from brainvisa.processes import defaultContext
from brainvisa.configuration import neuroConfig
from soma.wip.application.api import Application
from soma import aims


class SPMNormalization(object):
         
    @classmethod
    def run(cls, mri, commissure_coordinates, talairach_transformation):
        # run brainvisa with databases and logging disabled because these features
        # do not support parallel execution. 
        neuroConfig.fastStart = True
        neuroConfig.logFileName = ''
        brainvisa.axon.initializeProcesses()
        
        transformations_directory = os.path.dirname(talairach_transformation)
        mri_name = os.path.basename(mri)
        mri_name = mri_name.split(".")[0]
        mri_path = os.path.dirname(mri)
        try:
            talairach_mni_transform = os.path.join(transformations_directory, 
                                                   "RawT1_%s_TO_Talairach-MNI.trm" % mri_name)
            spm_transformation = os.path.join(mri_path, "%s_sn.mat" % mri_name)
            normalized_mri =  os.path.join(mri_path, "normalized_SPM_%s.nii" 
                                           % mri_name)
            configuration = Application().configuration
            spm_path = configuration.SPM.spm8_standalone_path
            if not spm_path:
                spm_path = configuration.SPM.spm8_path
            if not spm_path:
                spm_path = configuration.SPM.spm5_path
            spm_t1_template = os.path.join(spm_path, 
                                           "templates", "T1.nii")
            
            defaultContext().runProcess("SPMnormalizationPipeline", mri, 
                                        talairach_mni_transform, 
                                        spm_transformation, normalized_mri, 
                                        spm_t1_template)
            
            mri_referential = os.path.join(transformations_directory, 
                                           "RawT1-%s.referential" % mri_name)
            mri_referential_file = open(mri_referential, "w")
            mri_referential_file.write("attributes = {'uuid' : '%s'}" 
                                       % cls._get_referential_uuid(mri))
            mri_referential_file.close()
            brainvisa_share_directory = neuroConfig.dataPath[0].directory
            normalized_referential = os.path.join(brainvisa_share_directory,
                                                  "registration", 
                                                  "Talairach-MNI_template-SPM.referential")
            tr_acpc_to_normalized = os.path.join(brainvisa_share_directory,
                                                 "transformation", 
                                                 "talairach_TO_spm_template_novoxels.trm")
            acpc_referential = os.path.join(brainvisa_share_directory,
                                                 "registration", 
                                                 "Talairach-AC_PC-Anatomist.referential")
            
            defaultContext().runProcess("TalairachTransformationFromNormalization", 
                                        talairach_mni_transform, 
                                        talairach_transformation, 
                                        commissure_coordinates, 
                                        mri, mri_referential, 
                                        normalized_referential,
                                        tr_acpc_to_normalized, 
                                        acpc_referential)
            
            brainvisa.axon.cleanup()
        finally:
            for temp_filename in (talairach_mni_transform, spm_transformation, 
                                  normalized_mri, mri_referential):
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
        return neuroConfig.exitValue
  
    @staticmethod
    def _get_referential_uuid(image):
        vol = aims.read(image)
        if vol.header().has_key("referential"):
            ref = vol.header()["referential"]
        else:
            ref = uuid.uuid4()
        return ref
   
         
if __name__ == '__main__':
    
    parser = OptionParser(usage='%prog mri_file commissure_coordinates_file '
                          'talairach_transformation_file')
    options, args = parser.parse_args()
    if len(args) != 3:
        parser.error('Invalid arguments : mri_file, commissure_coordinates_file'
                     ' and talairach_transformation_file are mandatory.')
    normalization = SPMNormalization()
    mri = args[0]
    commissure_coordinates = args[1]
    talairach_transformation = args[2]
    normalization.run(mri, commissure_coordinates, talairach_transformation)
