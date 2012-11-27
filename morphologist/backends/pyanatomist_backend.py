import anatomist.direct.api as ana

from morphologist.gui.qt_backend import QtCore, QtGui, loadUi 
from morphologist.backends import Backend, DisplayManagerMixin


class PyanatomistBackend(Backend, DisplayManagerMixin):

    def __init__(self):
        super(PyanatomistBackend, self).__init__()
        super(DisplayManagerMixin, self).__init__()
        # must be instanciate after the Qt eventloop has been started

    def initialize_display(self):
        self.anatomist = ana.Anatomist('-b')

    def create_axial_view(self, parent=None):
        wintype = 'Axial'
        cmd = ana.cpp.CreateWindowCommand(wintype, -1, None,
                [], 1, parent, 2, 0,
                { '__syntax__' : 'dictionary',  'no_decoration' : 1})
        self.anatomist.execute(cmd)
        window = cmd.createdWindow()
        window.setWindowFlags(QtCore.Qt.Widget)
        awindow = self.anatomist.AWindow(self.anatomist, window)
        parent.layout().addWidget(awindow.getInternalRep())
        return window

    def set_bgcolor_views(self, views, rgba_color):
        # rgba_color must a list of 4 floats between 0 and 1
        self.anatomist.execute('WindowConfig',
                windows=views, cursor_visibility=0,
                light={'background' : rgba_color})
