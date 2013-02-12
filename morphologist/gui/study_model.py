from .qt_backend import QtCore


class LazyStudyModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    status_changed = QtCore.pyqtSignal()
    runner_status_changed = QtCore.pyqtSignal(bool) 

    def __init__(self, study=None, runner=None, parent=None):
        super(LazyStudyModel, self).__init__(parent)
        self.study = None
        self.runner = None
        self._subjects = []
        self._status = {}

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
        self._subjects = self.study.subjects
        self._subjects.sort()
        self._status = {}
        self._runner_is_running = False
        self._update_all_status()
        self.changed.emit()

    def get_status(self, index):
        subject = self._subjects[index]
        return self._status[subject]

    def get_subject(self, index):
        return self._subjects[index]

    def subject_count(self):
        return len(self._subjects)

    @QtCore.Slot()
    def _update_all_status(self):
        has_changed = False
        new_runner_status = self.runner.is_running()
        if new_runner_status != self._runner_is_running:
            self._runner_is_running = new_runner_status
            self.runner_status_changed.emit(self._runner_is_running)
        for subject in self._subjects:
            has_changed |= self._update_status_for_one_subject(subject) 
        if has_changed:
            self.status_changed.emit()

    def _update_status_for_one_subject(self, subject):
        has_changed = False
        if self.runner.is_running(subject, update_status=False):
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subject, "is running")
        elif self.runner.has_not_started():
            has_changed = self._update_output_files_status_for_one_subject_if_needed(subject)
        else:
            if self.runner.has_failed(subject, update_status=False):
                has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subject, "last run failed")
            else:
                has_changed = self._update_output_files_status_for_one_subject_if_needed(subject)
        return has_changed

    def _update_output_files_status_for_one_subject_if_needed(self,
                                                        subject):
        analysis = self.study.analyses[subject.id()]
        has_changed = False
        if not analysis.outputs.some_file_exists():
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subject, "no output files")
        elif analysis.outputs.all_file_exists():
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                            subject, "output files exist")
        else:
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                        subject, "some output files exist")
        return has_changed

    def _update_one_status_for_one_subject_if_needed(self, subject, status):
        has_changed = False 
        if self._status.get(subject) != status:
            self._status[subject] = status
            has_changed = True
        return has_changed
