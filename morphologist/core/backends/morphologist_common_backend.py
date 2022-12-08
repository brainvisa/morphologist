from __future__ import absolute_import
from brainvisa.morphologist.qt4gui.histo_analysis_widget \
    import load_histo_data, create_histo_view, HistoData
from brainvisa.morphologist.qt4gui.histo_analysis_editor import create_histo_editor

from morphologist.core.gui.qt_backend import QtGui
from morphologist.core.backends import Backend
from morphologist.core.backends.mixins import VectorGraphicsManagerMixin


class MorphologistCommonBackend(Backend, VectorGraphicsManagerMixin):
    
    def __init__(self):
        super(MorphologistCommonBackend, self).__init__()

### display
    def create_view(self, parent):
        return create_histo_view(parent)

    def clear_view(self, backend_view):
        backend_view.clear()

    def add_object_in_view(self, backend_object, backend_view):
        backend_view.set_histo_data(backend_object, nbins=100)
        backend_view.draw_histo()

    def set_bgcolor_view(self, backend_view, color):
        color = [int(round(x)) for x in color]
        palette = QtGui.QPalette(QtGui.QColor(*color))
        backend_view.setPalette(palette)

    def create_extended_view(self, parent):
        view = create_histo_editor()
        view.setParent(parent)
        if parent is not None:
            parent.layout().addWidget(view)
            if parent.parent() is not None:
                view.closed.connect(parent.parent().close)
        return view

    def add_object_in_editor(self, backend_object, backend_view):
        if isinstance( backend_object, HistoData ):
            backend_view.set_histo_data(backend_object, nbins=100)
        else:
            backend_view.set_bias_corrected_image( backend_object.fileName() )
            self.set_bgcolor_editor(backend_view, [0,0,0,1.])

    def set_bgcolor_editor(self, backend_view, color):
        color = [int(round(x)) for x in color]
        palette = QtGui.QPalette(QtGui.QColor(*color))
        backend_view.setPalette(palette)
        awin = backend_view.awindow()
        if awin is not None:
            anatomist = awin.anatomistinstance
            anatomist.execute('WindowConfig',
                windows=[awin], light={'background' : color})

### objects loader
    def load_histogram(self, filename):
        return load_histo_data(filename)
