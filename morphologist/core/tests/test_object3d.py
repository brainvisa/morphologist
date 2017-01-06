import unittest
import getpass
import os.path
import tempfile

from morphologist.core.gui.object3d import Object3D
from morphologist.core.backends.mixins import LoadObjectError
 

class TestObject3D(unittest.TestCase):

    @classmethod
    def get_test_dir(cls):
        test_dir = os.environ.get('BRAINVISA_TESTS_DIR')
        if not test_dir:
            raise RuntimeError('BRAINVISA_TESTS_DIR is not set')
        test_dir = os.path.join(test_dir, 'tmp_tests_brainvisa')
        return test_dir

    def setUp(self):
        pass


    def test_raise_load_object_error_volume(self):
        filename = os.path.join(self.get_test_dir(),
                                "data_unprocessed/sujet01/anatomy/sujet01.ima")
        truncated_filename = os.path.join(
            self.get_test_dir(), 'morphologist-ui', 'output_dirs',
            getpass.getuser(), 'morphologist_test_truncated_image.nii')

        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)


    def test_raise_load_object_error_surface(self):
        filename = os.path.join(
            self.get_test_dir(),
            "data_for_anatomist/subject01/subject01_Lwhite.mesh")
        truncated_filename = os.path.join(
            self.get_test_dir(), 'morphologist-ui', 'output_dirs',
            getpass.getuser(), 'morphologist_test_truncated_surface.gii')
        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)

    def test_raise_load_object_error_graph(self):
        filename = os.path.join(
            self.get_test_dir(),
            'data_for_anatomist/subject01/sulci/'
            'Lsubject01_default_session_auto.arg')
        truncated_filename = os.path.join(
            self.get_test_dir(), 'morphologist-ui', 'output_dirs',
            getpass.getuser(), 'morphologist_test_truncated_graph.arg')
        self._create_truncated_file(filename, truncated_filename)

        self.assertRaises(LoadObjectError,
                          Object3D.from_filename,
                          truncated_filename)

    def _create_truncated_file(self, filename, truncated_filename):
        ext = filename.split('.')[-1]
        tmp_file = None
        if truncated_filename.split('.')[-1] != ext:
            tmp_file = tempfile.mkstemp(suffix=ext, prefix='morpho')
            os.close(tmp_file[0])
            from soma import aims
            im = aims.read(filename)
            aims.write(im, tmp_file[1])
            filename = tmp_file[1]
            del im
        image_file = open(filename, "rb")
        image_piece = image_file.read(os.path.getsize(filename)/2)
        image_file.close()
        if tmp_file:
            os.unlink(tmp_file[1])
            del tmp_file

        path = os.path.dirname(truncated_filename)
        if not os.path.exists(path):
            os.makedirs(path)
        truncated_file = open(truncated_filename, "w")
        truncated_file.write(image_piece)
        truncated_file.close()

    def tearDown(self):
        pass


if __name__ == '__main__':

    unittest.main()


