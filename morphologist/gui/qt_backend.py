import sys, imp, __builtin__

def choose_pyqt_backend():
    import sip
    API_VERSION = 2
    qt_api = ["QDate", "QDateTime", "QString", "QTextStream", "QTime", "QUrl", "QVariant"]
    for qt_module in qt_api:
        sip.setapi(qt_module, API_VERSION)
    try:
        module_info = imp.find_module('PyQt4')
    except ImportError, e:
        raise Exception("error: missing PyQt dependency.")
    module = imp.load_module('PyQt4', *module_info)
    submodules = ['QtCore', 'QtGui', 'QtTest'] #TODO : add missing modules
    for submodule in submodules:
        __builtin__.__import__('PyQt4.' + submodule)
        globals()[submodule] = module.__getattribute__(submodule)
        
    import PyQt4.QtCore
    PyQt4.QtCore.Slot = PyQt4.QtCore.pyqtSlot
    PyQt4.QtCore.Signal = PyQt4.QtCore.pyqtSignal
    global loadUi
    def loadUi(uifile, baseinstance=None):
        from PyQt4 import uic
        return uic.loadUi(uifile, baseinstance=baseinstance)

def choose_pyside_backend():
    try:
        module_info = imp.find_module('PySide')
    except ImportError, e:
        raise Exception("error: missing PySide dependency.")
    module = imp.load_module('morphologist.gui.qt_backend', *module_info)

    global loadUi
    def loadUi(uifile, baseinstance=None):
        from PySide.QtUiTools import QUiLoader
        from PySide.QtCore import QMetaObject
        loader = QUiLoader(baseinstance)
        ui = loader.load(uifile)
        QMetaObject.connectSlotsByName(ui)
        return ui


# Choose the python bindings you want to use for QT :
# PyQt (API 2) or PySide
choose_pyqt_backend()
#choose_pyside_backend()
