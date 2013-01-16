from .qt_backend import QtCore


class LazyStudyModel(QtCore.QObject):
    changed = QtCore.pyqtSignal()
    status_changed = QtCore.pyqtSignal()
    runner_status_changed = QtCore.pyqtSignal(bool) 

    def __init__(self, study=None, runner=None, parent=None):
        super(LazyStudyModel, self).__init__(parent)
        self.study = None
        self.runner = None
        self._subjectnames = []
        self._status = {}

        self._update_interval = 2 # in seconds
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(self._update_interval * 1000)
        if study is not None and runner is not None:
            self.set_study(study, runner)
        self._timer.start()

    def set_study_and_runner(self, study, runner):
        if self.runner is None:
            self.runner = runner
            self._timer.timeout.connect(self._update_all_status)
        else:
            self.runner = runner
        self.study = study
        self._subjectnames = self.study.subjects.keys()
        self._subjectnames.sort()
        self._status = {}
        self._runner_is_running = False
        self._update_all_status()
        self.changed.emit()

    def get_status(self, index):
        subjectname = self._subjectnames[index]
        return self._status[subjectname]

    def get_subjectname(self, index):
        return self._subjectnames[index]

    def subject_count(self):
        return len(self._subjectnames)

    @QtCore.Slot()
    def _update_all_status(self):
        has_changed = False
        new_runner_status = self.runner.is_running()
        if new_runner_status != self._runner_is_running:
            self._runner_is_running = new_runner_status
            self.runner_status_changed.emit(self._runner_is_running)
        for subjectname in self._subjectnames:
            has_changed |= self._update_status_for_one_subject(subjectname) 
        if has_changed:
            self.status_changed.emit()

    def _update_status_for_one_subject(self, subjectname):
        analysis = self.study.analyses[subjectname]
        has_changed = False
        if self.runner.is_running(subjectname):
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subjectname, "is running")
        elif self.runner.last_run_failed():
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subjectname, "last run failed")
        elif len(analysis.outputs.list_existing_files()) == 0:
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                                subjectname, "no output files")
        elif len(analysis.outputs.list_missing_files()) == 0:
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                            subjectname, "output files exist")
        else:
            has_changed = self._update_one_status_for_one_subject_if_needed(\
                                        subjectname, "some output files exist")
        return has_changed

    def _update_one_status_for_one_subject_if_needed(self, subjectname, status):
        has_changed = False 
        if self._status.get(subjectname) != status:
            self._status[subjectname] = status
            has_changed = True
        return has_changed
