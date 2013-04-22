from morphologist.core.gui.qt_backend import QtCore
from morphologist.core.gui.study_editor import StudyEditor
from morphologist.core.gui.study_editor_widget import StudyEditorDialog, \
                                                    SelectOrganizedDirectoryDialog


class ImportStudyDialog(SelectOrganizedDirectoryDialog):
    
    def __init__(self, parent, default_directory, analysis_type,
                 selected_template_name):
        super(ImportStudyDialog, self).__init__(parent, default_directory, 
                                                analysis_type, selected_template_name)
        self.ui.in_place_checkbox.setVisible(True)
        
    def is_import_in_place_selected(self):
        return self.ui.in_place_checkbox.checkState() == QtCore.Qt.Checked 
    

class ImportStudyEditorDialog(StudyEditorDialog):
    
    def __init__(self, study, parent=None, in_place=True, subjects=None):
        if in_place:
            mode = StudyEditor.EDIT_STUDY
        else:
            mode = StudyEditor.NEW_STUDY
        super(ImportStudyEditorDialog, self).__init__(study, parent, mode)
        if subjects:
            self._subjects_tablemodel.add_subjects(subjects)
            