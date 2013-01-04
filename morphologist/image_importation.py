import shutil
import os
import tempfile
from optparse import OptionParser

from soma import aims


class Importer:
    
    @classmethod
    def import_t1mri(cls, input_filename, output_filename): 
        temp_input = None
        return_value = 0
        
        try:
            input_vol = aims.read(input_filename)
        except (aims.aimssip.IOError, IOError) as e:
            raise ImportationError(e.message)
    
        if cls._conversion_needed(input_filename, input_vol, output_filename):
            try:
                if cls._remove_nan_needed(input_vol):
                    (temp_file, temp_input) = tempfile.mkstemp()
                    temp_file.close()
                    command = "AimsRemoveNaN -i '%s' -o '%s'" % (input_filename, temp_input)
                    return_value = os.system(command)
                    if return_value != 0:
                        raise ImportationError("The following command failed : %s" % command)
                    input_filename = temp_input
    
                command_list = ['AimsFileConvert', '-i', input_filename, '-o', output_filename, 
                           '-t', 'S16']
                if cls._resampling_needed(input_vol):
                    command_list.extend([ '-r', '--omin', 0, '--omax', 4095 ])
                command = " ".join(command_list)
                return_value = os.system(command)
                if return_value != 0:
                    raise ImportationError("The following command failed : %s" % command)
            finally:
                if temp_input is not None:
                    os.remove(temp_input)                
    
        else:
            try:
                shutil.copy(input_filename, output_filename)
                if os.path.exists(input_filename+".minf"):
                    shutil.copy(input_filename+".minf", output_filename+".minf")
            except IOError as e:
                raise ImportationError(e.message)
        return return_value
    
    @classmethod
    def _conversion_needed(cls, input_filename, input_vol, output_filename):
        convert = False
        
        if (cls._file_extension(input_filename) != cls._file_extension(output_filename)):
            convert = True
        else:
            header = input_vol.header()
            data_type = header["data_type"]
            file_format = header["file_type"] 
            convert = ((file_format != "NIFTI1") and (file_format != 'GIS')) \
                        or (data_type != "S16")
        return convert
      
    @staticmethod
    def _file_extension(filename):
        extension = ""
        name, ext = os.path.splitext(filename)
        while ext:
            extension = ext + extension
            name, ext = os.path.splitext(name)
        return extension
        
    @staticmethod  
    def _resampling_needed(input_vol):
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
    def _remove_nan_needed(input_vol):
        header = input_vol.header()
        data_type=header["data_type"]
        return data_type in ('FLOAT', 'DOUBLE')
                 
     
class ImportationError(Exception):
    pass   
        
        
if __name__ == '__main__':
    
    parser = OptionParser(usage='%prog input_file output_file')
    options, args = parser.parse_args()
    if len(args) != 2:
        parser.error('Invalid arguments : input_file and output_file are mandatory.')
    Importer.import_t1mri(args[0], args[1])

