import unittest
import getpass
import os.path

from morphologist.gui.object3d import Object3D
from morphologist.backends.mixins import LoadObjectError
 

class TestObject3D(unittest.TestCase):

    def setUp(self):
        pass


    def test_raise_load_object_error_volume(self):
        filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"       
        truncated_filename = os.path.join('/neurospin', 'tmp', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(),
                                      'morphologist_test_truncated_image.nii')
        
        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)


    def test_raise_load_object_error_surface(self):
        filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/"\
        +"test/hyperion/t1mri/default_acquisition/default_analysis/segmentation/mesh/"\
        +"hyperion_Lwhite.gii"       
        truncated_filename = os.path.join('/neurospin', 'tmp', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(),
                                      'morphologist_test_truncated_surface.gii')
        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)

    def test_raise_load_object_error_graph(self):
        filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/bv_database/"\
        +"test/hyperion/t1mri/default_acquisition/default_analysis/folds/3.1/Lhyperion.arg"
        truncated_filename = os.path.join('/neurospin', 'tmp', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(),
                                      'morphologist_test_truncated_graph.arg')
        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)
        
    def _create_truncated_file(self, filename, truncated_filename):
        image_file = open(filename, "rb")
        image_peace = image_file.read(os.path.getsize(filename)/2)
        image_file.close()

        truncated_file = open(truncated_filename, "w")
        truncated_file.write(image_peace)
        truncated_file.close()
        
    def tearDown(self):
        pass


if __name__ == '__main__':

    unittest.main()


