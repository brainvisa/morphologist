from morphologist.core.gui.qt_backend import QtCore
from morphologist.core.constants import ALL_SUBJECTS


class LazyStudyModel(QtCore.QObject):
    DEFAULT_STATUS = ''
    changed = QtCore.pyqtSignal()
    status_changed = QtCore.pyqtSignal()
    runner_status_changed = QtCore.pyqtSignal(bool)
    current_subject_changed = QtCore.pyqtSignal()
    subject_selection_changed = QtCore.pyqtSignal(int)


    def __init__(self, study, runner, parent=None):
        super(LazyStudyModel, self).__init__(parent)
        self._init_study_and_runner(study, runner)
        self._update_interval = 2 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        self._timer.timeout.connect(self._update_all_status)
        self._timer.start()

    def _init_study_and_runner(self, study, runner):
        self.runner = runner
        self.study = study
        self._subjects_row_index_to_id = [] # row index -> id
        self._status = []                   # row index -> status
        self._are_selected_subjects = []    # row index -> is_selected
        self._current_subject_index = None
        for subject_id, _ in self.study.subjects.iteritems():
            self._subjects_row_index_to_id.append(subject_id)
            self._status.append(self.DEFAULT_STATUS)
            self._are_selected_subjects.append(False)
        self.set_current_subject_index(0)
        self._runner_is_running = False
        self._update_all_status()
    
    def set_study_and_runner(self, study, runner):
        self._init_study_and_runner(study, runner)
        self.changed.emit()

    @property
    def runner_is_running(self):
        return self._runner_is_running
    
    def get_status(self, row_index):
        return self._status[row_index]

    def get_subject(self, row_index):
        subject_id = self._subjects_row_index_to_id[row_index]
        subject = self.study.subjects[subject_id]
        return subject

    def get_selected_subject_ids(self):
        selected_subject_ids = []
        for index, subject_id in enumerate(self._subjects_row_index_to_id):
            if self._are_selected_subjects[index]:
                selected_subject_ids.append(subject_id)
        if not selected_subject_ids:
            selected_subject_ids = ALL_SUBJECTS
        return selected_subject_ids
 
    def set_selected_subject(self, row_index, selected):
        self._are_selected_subjects[row_index] = selected
        self.subject_selection_changed.emit(row_index)
            
    def is_selected_subject(self, row_index):
        return self._are_selected_subjects[row_index]
            
    def get_current_subject_id(self):
        if self._subjects_row_index_to_id:
            return self._subjects_row_index_to_id[self._current_subject_index]
        return None
                 
    def get_current_subject_index(self):
        return self._current_subject_index
    
    def set_current_subject_index(self, row_index):
        if row_index != self._current_subject_index:
            self._current_subject_index = row_index
            self.current_subject_changed.emit()
        
    def subject_count(self):
        return len(self._subjects_row_index_to_id)

    @QtCore.Slot()
    def _update_all_status(self):
        has_changed = False
        new_runner_status = self.runner.is_running()
        if new_runner_status != self._runner_is_running:
            self._runner_is_running = new_runner_status
            self.runner_status_changed.emit(self._runner_is_running)
        for row_index, _ in enumerate(self._subjects_row_index_to_id):
            has_changed |= self._update_subject_status(row_index) 
        if has_changed:
            self.status_changed.emit()

    def _update_subject_status(self, row_index):
        has_changed = False
        subject_id = self._subjects_row_index_to_id[row_index]
        if self.runner.is_running(subject_id, update_status=False):
            has_changed = self._update_subject_status_if_needed(row_index, "is running")
        elif self.runner.has_failed(subject_id, update_status=False):
            step_ids = self.runner.get_failed_step_ids(subject_id, update_status=False)
            step_id = step_ids[0]
            step_name = self.study.analyses[subject_id].step_from_name(step_id).name
            has_changed = self._update_subject_status_if_needed(row_index, "failed at %s" % step_name)
        else:
            has_changed = self._update_subject_output_files_status_if_needed(row_index)
        return has_changed

    def _update_subject_output_files_status_if_needed(self, row_index):
        subject_id = self._subjects_row_index_to_id[row_index]
        analysis = self.study.analyses[subject_id]
        has_changed = False
        if not analysis.outputs.some_file_exists():
            has_changed = self._update_subject_status_if_needed(row_index, "no output files")
        elif analysis.outputs.all_file_exists():
            has_changed = self._update_subject_status_if_needed(row_index, "output files exist")
        else:
            has_changed = self._update_subject_status_if_needed(row_index, "some output files exist")
        return has_changed

    def _update_subject_status_if_needed(self, row_index, status):
        has_changed = False 
        if self._status[row_index] != status:
            self._status[row_index] = status
            has_changed = True
        return has_changed
