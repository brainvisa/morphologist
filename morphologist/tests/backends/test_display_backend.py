import unittest
import getpass
import os.path

from morphologist.gui.object3d import Object3D
from morphologist.backends.mixins import LoadObjectError
 

class TestDisplayBackend(unittest.TestCase):

    def setUp(self):
        pass


    def test_raise_load_object_error(self):
        filename = "/neurospin/lnao/Panabase/cati-dev-prod/morphologist/raw_irm/hyperion.nii"       
        truncated_filename = os.path.join('/neurospin', 'tmp', 
                                      'cati-dev-prod', 'morphologist', 
                                      'output_dirs', getpass.getuser(),
                                      'morphologist_test_truncated_image.nii')
        image_file = open(filename, "rb")
        image_peace = image_file.read(os.path.getsize(filename)/2)
        image_file.close()

        truncated_file = open(truncated_filename, "w")
        truncated_file.write(image_peace)
        truncated_file.close() 

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)

    def tearDown(self):
        pass


if __name__ == '__main__':

    unittest.main()


