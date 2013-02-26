from morphologist.core.gui.qt_backend import QtCore
from morphologist.core.runner import Runner


class LazyStudyModel(QtCore.QObject):
    DEFAULT_STATUS = ''
    changed = QtCore.pyqtSignal()
    status_changed = QtCore.pyqtSignal()
    runner_status_changed = QtCore.pyqtSignal(bool) 

    def __init__(self, study=None, runner=None, parent=None):
        super(LazyStudyModel, self).__init__(parent)
        self.study = None
        self.runner = None
        self._subjects_row_index_to_id = [] # row index
        self._status = []                   # row index

        self._update_interval = 2 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        if study is not None and runner is not None:
            self.set_study_and_runner(study, runner)
        self._timer.start()

    def set_study_and_runner(self, study, runner):
        if self.runner is None:
            self.runner = runner
            self._timer.timeout.connect(self._update_all_status)
        else:
            self.runner = runner
        self.study = study
        self._subjects_row_index_to_id = []
        self._status = []
        for subject_id, subject in self.study.subjects.iteritems():
            self._subjects_row_index_to_id.append(subject_id)
            self._status.append(self.DEFAULT_STATUS)
        self._runner_is_running = False
        self._update_all_status()
        self.changed.emit()

    def get_status(self, row_index):
        return self._status[row_index]

    def get_subject(self, row_index):
        subject_id = self._subjects_row_index_to_id[row_index]
        subject = self.study.subjects[subject_id]
        return subject

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
            has_changed |= self._update_status_for_one_subject(row_index) 
        if has_changed:
            self.status_changed.emit()

    def _update_status_for_one_subject(self, row_index):
        has_changed = False
        subject_id = self._subjects_row_index_to_id[row_index]
        subject = self.study.subjects[subject_id]
        if self.runner.is_running(subject, update_status=False):
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                row_index, "is running")
        elif self.runner.has_failed(subject, update_status=False):
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                row_index, "last run failed")
        else:
            has_changed = self._update_output_files_status_for_one_subject_if_needed(row_index)
        return has_changed

    def _update_output_files_status_for_one_subject_if_needed(self, row_index):
        subject_id = self._subjects_row_index_to_id[row_index]
        analysis = self.study.analyses[subject_id]
        has_changed = False
        if not analysis.outputs.some_file_exists():
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                row_index, "no output files")
        elif analysis.outputs.all_file_exists():
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                            row_index, "output files exist")
        else:
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                        row_index, "some output files exist")
        return has_changed

    def _update_one_status_for_one_subject_if_needed(self, row_index, status):
        has_changed = False 
        if self._status[row_index] != status:
            self._status[row_index] = status
            has_changed = True
        return has_changed
