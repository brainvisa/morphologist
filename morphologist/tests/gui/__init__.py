import types
import unittest

from morphologist.gui.qt_backend import QtCore, QtGui
from morphologist import settings

if settings['start_qt_event_loop_for_tests']:
    class TestGui(unittest.TestCase):

        @staticmethod
        def start_qt_and_test(test):
            def func(self):
                timer = QtCore.QTimer()
                func = types.MethodType(test, self, self.__class__)
                timer.singleShot(0, func)
                self.assertFalse(QtGui.qApp.exec_())
            return func
else:
    class TestGui(unittest.TestCase):

        @staticmethod
        def start_qt_and_test(test):
            def func(self):
                test(self)
            return func
