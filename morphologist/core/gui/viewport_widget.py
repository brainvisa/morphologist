import os

from morphologist.core.backends.mixins import LoadObjectError, ViewType
from morphologist.core.gui.object3d import Object3D, View
from morphologist.core.gui.vector_graphics import VectorView
from morphologist.core.gui.qt_backend import QtCore, QtGui, loadUi
from morphologist.core.gui import ui_directory 


class AnalysisViewportModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    parameter_changed = QtCore.pyqtSignal(list)
    use_async_load = False

    class LoadCallback(object):
        def __init__(self, viewport_model, parameter_name):
            self._viewport_model = viewport_model
            self._parameter_name = parameter_name

        def object_loaded(self, object3d):
            self._viewport_model._observed_object_loaded(self._parameter_name,
                object3d, self)

    def __init__(self, model):
        super(AnalysisViewportModel, self).__init__()
        self._init_model(model)
        self._init_3d_objects()
        self._load_callbacks = set()

    def _init_model(self, model):
        self._analysis_model = model
        self._analysis_model.changed.connect(self.on_analysis_model_changed)
        self._analysis_model.files_changed.connect(\
                self.on_analysis_model_files_changed)

    def _init_3d_objects(self):
        self.observed_objects = {}
        raise NotImplementedError("SubjectwiseViewportModel is an abstract class")

    @QtCore.Slot()
    def on_analysis_model_changed(self):
        # XXX : may need a cache ?
        self._init_3d_objects()
        self.changed.emit()

    @QtCore.Slot(dict)
    def on_analysis_model_files_changed(self, changed_parameters):
        updated_parameters = []
        self._remove_useless_parameters(changed_parameters)
        for parameter_name, filename in changed_parameters.iteritems():
            if parameter_name in self.observed_objects.keys():
                self._update_observed_objects(parameter_name, filename)
                if not self.use_async_load:
                    updated_parameters.append(parameter_name)
        if not self.use_async_load:
            self.parameter_changed.emit(updated_parameters)

    def _update_observed_objects(self, parameter_name, filename):
        object3d = self.observed_objects[parameter_name]
        if object3d is not None:
            if os.path.exists(filename):
                object3d.reload()
            else:
                object3d = None
        else:
            try:
                if self.use_async_load:
                    callback = AnalysisViewportModel.LoadCallback(self,
                        parameter_name)
                    self._load_callbacks.add( callback )
                    self.load_object_async(parameter_name, filename,
                        callback.object_loaded)
                else:
                    # sync load, no callback
                    object3d = self.load_object(parameter_name, filename)
            except LoadObjectError:
                object3d = None
        if not self.use_async_load:
            self.observed_objects[parameter_name] = object3d

    def _observed_object_loaded(self, parameter_name, object3d, callback):
        self.observed_objects[parameter_name] = object3d
        self._load_callbacks.remove(callback)
        self.parameter_changed.emit([parameter_name])

    @staticmethod
    def load_object(parameter_name, filename):
        _ = parameter_name
        return Object3D.from_filename(filename)

    @staticmethod
    def load_object_async(parameter_name, filename, callback):
        _ = parameter_name
        Object3D.from_filename_async(filename, callback)

    def _remove_useless_parameters(self, changed_parameters):
        pass


class AnalysisViewportWidget(QtGui.QFrame):
    style_sheet = '''
        #viewport_widget {
            background: white;
        }
        '''
    
    def __init__(self, model, parent=None):
        super(AnalysisViewportWidget, self).__init__(parent)
        self.setObjectName("viewport_widget")
        self._init_widget()
        self._views = []
        self._init_views(model)
    
    def _init_widget(self):
        self._grid_layout = QtGui.QGridLayout(self)
        self._grid_layout.setMargin(3)
        self._grid_layout.setSpacing(3)
        self.setStyleSheet(self.style_sheet)

    def _init_views(self, model):
        raise NotImplementedError("AnalysisViewportWidget is an abstract class.")

    def set_object3d_views_view_type(self, view_type):
        for view in self._views:
            if isinstance(view, Object3DViewportView):
                view.set_view_type(view_type)
    
    
class ViewportView(QtGui.QFrame):
    uifile = os.path.join(ui_directory, 'viewport_view.ui')
    bg_color = [0., 0., 0., 1.]
    frame_style_sheet = '''
        #view_frame {
            border: 3px solid black;
            border-radius: 10px;
            background: black;
        }
        #view_label {
            color: white;
            background: black;
        }
        QLabel {
            color: white;
            background-color: black;
        }
        QSlider {
            color: white;
            background-color: black;
        }
        QSlider::handle {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #909090, stop:1 #202020);
            border: 0px;
            height: 12px;
            width: 12px;
            margin: -4px;
            border-radius: 6px;
        }
        QSlider::handle:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b0b0b0, stop:1 #404040);
            border-width: 1px;
            border-style: solid;
            border-color: #00f0ff;
        }
        QSlider::groove:vertical {
            border-width: 1px;
            border-radius: 3px;
            border-style: solid;
            border-color: #202020 gray gray #202020;
            width: 4px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #303030, stop:1 #505050);
            margin: 6px;
        }
        QSlider::groove:horizontal {
            border-width: 1px;
            border-radius: 3px;
            border-style: solid;
            border-color: #202020 gray gray #202020;
            height: 4px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #303030, stop:1 #505050);
            margin: 6px;
        }
        QGraphicsView {
            background: black;
        }
    '''

    def __init__(self, model, parent=None):
        super(ViewportView, self).__init__(parent)
        self.ui = loadUi(self.uifile, self)
        self._view = None
        self._observed_parameters = []
        self._init_widget()
        self._init_model(model)

    def _init_widget(self):
        self.ui.setStyleSheet(self.frame_style_sheet)
        layout = QtGui.QVBoxLayout(self.ui.view_hook)
        layout.setMargin(0)
        layout.setSpacing(0)
                
    def _init_model(self, model):
        self._viewport_model = model
        self._viewport_model.changed.connect(self.on_model_changed)
        self._viewport_model.parameter_changed.connect(self.on_parameter_changed)
        
    def set_title(self, title):
        self.ui.view_label.setText(title)
        
    def set_tooltip(self, tooltip):
        self.ui.view_label.setToolTip(tooltip)

    @QtCore.Slot()
    def on_model_changed(self):
        self._view.clear()
    
    @QtCore.Slot(list)
    def on_parameter_changed(self, changed_parameter_names):
        for parameter_name in self._observed_parameters:
            if parameter_name in changed_parameter_names:
                self.update()
                break
    
    def update(self):
        self._view.clear()
        for parameter_name in self._observed_parameters:
            observed_object \
                = self._viewport_model.observed_objects[parameter_name]
            if observed_object is not None:
                self._view.add_object(observed_object)
    
    # This slot is automagically connected
    @QtCore.Slot()            
    def on_extend_view_button_clicked(self):
        window = self.create_extended_view()
        window.show()
        
    def create_extended_view(self):
        window = self.__class__(self._viewport_model, self)
        window.setWindowFlags(QtCore.Qt.Window)
        window.ui.extend_view_button.setVisible(False)
        window.update()
        return window
    
    
class Object3DViewportView(ViewportView):
    
    def __init__(self, model, parent=None, view_type=ViewType.AXIAL, 
                 restricted_controls=True):
        super(Object3DViewportView, self).__init__(model, parent)
        self._view = View(self.ui.view_hook, view_type, restricted_controls)
        self._view.set_bgcolor(self.bg_color)
        # XXX The view update method might need to create new object (eg. fusion)
        # Such object is stored in temp_object to prevent its deletion (due to Anatomist backend).
        self._temp_object = None
    
    def on_model_changed(self):
        super(Object3DViewportView, self).on_model_changed()
        self._temp_object = None
        if self._view.view_type != ViewType.THREE_D:
                self._view.reset_camera()
                
    def create_extended_view(self):
        window = ExtendedObject3DViewportView(self._viewport_model, 
                                              view_class=self.__class__,
                                              parent=self)
        window.setWindowFlags(QtCore.Qt.Window)
        return window
    
    def set_view_type(self, view_type):
        if self._view.view_type != ViewType.THREE_D:
            self._view.view_type = view_type
          
          
class ExtendedObject3DViewportView(AnalysisViewportWidget):
    
    def __init__(self, model, view_class, parent=None):
        self._view_class = view_class
        super(ExtendedObject3DViewportView, self).__init__(model, parent)
        
    def _init_views(self, model):
        for view_type, line, column in [(ViewType.CORONAL, 0, 0), 
                                        (ViewType.SAGITTAL, 0, 1), 
                                        (ViewType.AXIAL, 1, 0), 
                                        (ViewType.THREE_D, 1, 1)]:
            view = self._view_class(model, parent=self, view_type=view_type, 
                                    restricted_controls=False)
            view.ui.extend_view_button.setVisible(False)
            view.ui.view_label.setVisible(False)
            view.update()
            self._grid_layout.addWidget(view, line, column)
        self.setWindowTitle(view.ui.view_label.text())
          
                
class VectorViewportView(ViewportView):
    
    def __init__(self, model, parent=None):
        super(VectorViewportView, self).__init__(model, parent)
        self._view = VectorView(self.ui.view_hook)
        self._view.set_bgcolor(self.bg_color)
