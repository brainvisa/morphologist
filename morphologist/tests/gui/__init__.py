import types
import unittest

from morphologist.core.gui.qt_backend import QtCore, QtGui
from morphologist.core.settings import settings


class TestGuiBase(unittest.TestCase):
    _widgets_kept_alive = []

    @classmethod
    def keep_widget_alive(cls, widget):
        cls._widgets_kept_alive.append(widget)
        

if settings['debug']['start_qt_event_loop_for_tests']:
    class TestGui(TestGuiBase):

        @staticmethod
        def start_qt_and_test(test):
            def func(self):
                timer = QtCore.QTimer()
                func = types.MethodType(test, self, self.__class__)
                timer.singleShot(0, func)
                self.assertFalse(QtGui.qApp.exec_())
            return func
else:
    class TestGui(TestGuiBase):

        @staticmethod
        def start_qt_and_test(test):
            def func(self):
                test(self)
            return func
