import shutil
import os
import tempfile
from optparse import OptionParser

from soma import aims

from .steps import Step


class ImageImportation(Step):
    
    def __init__(self):
        super(ImageImportation, self).__init__()
        
        self.input = None
        
        self.output = None
        
    def get_command(self):
        command = ["python", "-m", "morphologist.image_importation", 
                   self.input, 
                   self.output]
        return command
    
    @staticmethod
    def conversion_needed(input_filename, input_vol):
        convert = False
        if not input_filename.endswith(".nii"):
            convert = True
        else:
            header = input_vol.header()
            data_type=header["data_type"]
            file_format = header["file_type"] 
            convert = (file_format != "NIFTI1") or (data_type != "S16")
        return convert
      
    @staticmethod  
    def resampling_needed(input_vol):
        header = input_vol.header()
        data_type=header["data_type"]
        need_resampling = False
        if data_type in ('FLOAT', 'DOUBLE'):
            need_resampling = True
        else:
            min_value = input_vol.arraydata().min()
            max_value = input_vol.arraydata().max()
            if (min_value < 0) or (max_value < 100) or (max_value > 20000):
                need_resampling = True
        return need_resampling
    
    @staticmethod
    def remove_nan_needed(input_vol):
        header = input_vol.header()
        data_type=header["data_type"]
        return data_type in ('FLOAT', 'DOUBLE')
            
    def run(self):
        print "Run image importation step on ", self.input, self.output    
        temp_input = None
        input_filename = self.input
        return_value = 0
        
        try:
            input_vol = aims.read(self.input)
            if self.conversion_needed(input_filename, input_vol):
                if self.remove_nan_needed(input_vol):
                    (temp_file, temp_input) = tempfile.mkstemp()
                    temp_file.close()
                    command = "AimsRemoveNaN -i '%s' -o '%s'" % (self.input, temp_input)
                    return_value = os.system(command)
                    if return_value != 0:
                        raise ImportationError("The following command failed : %s" % command)
                    input_filename = temp_input

                command_list = ['AimsFileConvert', '-i', input_filename, '-o', self.output, 
                           '-t', 'S16']
                if self.resampling_needed(input_vol):
                    command_list.extend([ '-r', '--omin', 0, '--omax', 4095 ])
                command = " ".join(command_list)
                return_value = os.system(command)
                if return_value != 0:
                    raise ImportationError("The following command failed : %s" % command)

            else:
                shutil.copy(self.input, self.output)
                if os.path.exists(self.input+".minf"):
                    shutil.copy(self.input+".minf", self.output+".minf")
        except Exception, e:
            raise ImportationError(e.message)
        finally:
            if temp_input is not None:
                os.remove(temp_input)
        
        return return_value
     
     
class ImportationError(Exception):
    pass   
        
if __name__ == '__main__':
    
    parser = OptionParser(usage='%prog input_file output_file')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Invalid arguments : input_file and output_file are mandatory.')
    importation = ImageImportation()
    importation.input = args[0]
    importation.output = args[1]
    importation.run()