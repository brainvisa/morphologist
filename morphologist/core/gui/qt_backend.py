import sip
API_VERSION = 2
qt_api = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
for qt_module in qt_api:
    sip.setapi(qt_module, API_VERSION)

try:
    import PyQt4
except ImportError:
    raise Exception("error: missing PyQt dependency.")
else:
    from PyQt4 import QtCore, QtGui, QtTest, Qt, QtWebKit

import PyQt4.QtCore
PyQt4.QtCore.Slot = PyQt4.QtCore.pyqtSlot
PyQt4.QtCore.Signal = PyQt4.QtCore.pyqtSignal


def loadUi(uifile, baseinstance=None):
    from PyQt4 import uic
    return uic.loadUi(uifile, baseinstance=baseinstance)


def loadUiType(uifile):
    from PyQt4 import uic
    return uic.loadUiType(uifile)
