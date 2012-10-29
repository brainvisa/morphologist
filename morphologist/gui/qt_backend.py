import sys, imp

def choose_pyqt_backend():
    import sip
    API_VERSION = 2
    qt_api = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for qt_module in qt_api:
        sip.setapi(qt_module, API_VERSION)
    try:
        module = imp.find_module('PyQt')
    except ImportError, e:
        raise Exception("missing PyQt dependency.")
    import PyQt.QtCore
    PyQt.QtCore.Slot = QtCore.pyqtSlot
    PyQt.QtCore.Signal = QtCore.pyqtSignal
    return module

def choose_pyside_backend():
    try:
        return imp.find_module('PySide')
    except ImportError, e:
        raise Exception("missing PySide dependency.")


# Choose the python bindings you want to use for QT :
# PyQt (API 2) or PySide
#choose_pyqt_backend()
module = choose_pyside_backend()
imp.load_module('morphologist.gui.qt_backend', *module)
