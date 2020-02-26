
from __future__ import print_function

# select Qt backend matching the one used by anatomist
from __future__ import absolute_import
import anatomist.direct.api
from soma.qt_gui import qt_backend
qt_backend.set_qt_backend(compatible_qt5=True)
print("qt backend:", qt_backend.get_qt_backend())

from soma.qt_gui.qt_backend import QtCore, QtGui, QtTest, Qt, QtWebKit
from soma.qt_gui.qt_backend import loadUi, loadUiType

#import sip
#API_VERSION = 2
#qt_api = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
#for qt_module in qt_api:
    #sip.setapi(qt_module, API_VERSION)

#try:
    #import PyQt4
#except ImportError:
    #raise Exception("error: missing PyQt dependency.")
#else:
    #from PyQt4 import QtCore, QtGui, QtTest, Qt, QtWebKit

#import PyQt4.QtCore
#PyQt4.QtCore.Slot = PyQt4.QtCore.pyqtSlot
#PyQt4.QtCore.Signal = PyQt4.QtCore.pyqtSignal


#def loadUi(uifile, baseinstance=None):
    #from PyQt4 import uic
    #return uic.loadUi(uifile, baseinstance=baseinstance)


#def loadUiType(uifile):
    #from PyQt4 import uic
    #return uic.loadUiType(uifile)
