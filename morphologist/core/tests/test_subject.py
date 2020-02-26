from __future__ import absolute_import
import unittest

from morphologist.core.subject import Subject


class TestSubject(unittest.TestCase):
    
    def setUp(self):
        self.subjectname = "subject"
        self.groupname = "group"
        self.filename = "/tmp/filename.nii"

    def test_subjects_equal(self):
        subject1 = Subject(self.subjectname, self.groupname, self.filename)
        subject2 = Subject(self.subjectname, self.groupname, self.filename)

        self.assert_(subject1 == subject2)

    def test_subjects_not_equal(self):
        subject1 = Subject(self.subjectname, self.groupname, self.filename)
        subject2 = Subject(self.subjectname+"2", self.groupname, self.filename)
        subject3 = Subject(self.subjectname, self.groupname+"2", self.filename)
        subject4 = Subject(self.subjectname, self.groupname, self.filename+"2")

        self.assert_(subject1 != subject2)
        self.assert_(subject1 != subject3)
        self.assert_(subject1 != subject4)

    def test_copy_subject(self):
        subject1 = Subject(self.subjectname, self.groupname, self.filename)
        subject2 = subject1.copy()

        self.assert_(subject1 == subject2)

    def test_subjects_same_id(self):
        subject1 = Subject(self.subjectname, self.groupname, self.filename)
        subject2 = Subject(self.subjectname, self.groupname, self.filename+"2")

        self.assert_(subject1.id() == subject2.id())

    def test_subjects_different_id(self):
        subject1 = Subject(self.subjectname, self.groupname, self.filename)
        subject2 = Subject(self.subjectname+"2", self.groupname, self.filename+"2")

        self.assert_(subject1.id() != subject2.id())        


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSubject)
    unittest.TextTestRunner(verbosity=2).run(suite)

