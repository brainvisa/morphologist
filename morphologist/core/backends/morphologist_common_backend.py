from morphologist_common.gui.histo_analysis_widget import load_histo_data, \
                                                          create_histo_view

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
        palette = QtGui.QPalette(QtGui.QColor(*color))
        backend_view.setPalette(palette)

### objects loader
    def load_histogram(self, filename):
        return load_histo_data(filename)
