# -*- coding: utf-8 -*-
import os
import time
import threading
import multiprocessing

import soma.workflow as sw
from soma.workflow.client import WorkflowController, Helper, Workflow, Job, Group

from morphologist.core.settings import settings
from morphologist.core.utils import BidiMap
from morphologist.core.constants import ALL_SUBJECTS


# XXX:
# Now, step terminaison is assessed by:
#      1) the existance of some outputcomes (files)
#   or 2) the success of command (exit value = 0)
#
# An alternative would be to follow each external command by the creation of
# a file or by filling a log, something created by the runner of which value
# can be checked by him to assess without any doubt the step is finished.


class Runner(object):
    ''' Abstract class '''
    NOT_STARTED = 0x0
    RUNNING = 0x1
    FAILED = 0x2
    SUCCESS = 0x4
    STOPPED_BY_USER = 0x8
    UNKNOWN = 0x10
    INTERRUPTED = FAILED | STOPPED_BY_USER
    
    def __init__(self, study):
        super(Runner, self).__init__()
        self._study = study

    def run(self, subject_ids=ALL_SUBJECTS):
        raise NotImplementedError("Runner is an abstract class.")
    
    def is_running(self, subject_id=None, step_id=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")
    
    def get_running_step_ids(self, subject_id, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")
        
    def wait(self, subject_id=None, step_id=None):
        raise NotImplementedError("Runner is an abstract class.")
    
    def has_failed(self, subject_id=None, step_id=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")

    def get_failed_step_ids(self, subject_id, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")
    
    def stop(self, subject_id=None, step_id=None):
        raise NotImplementedError("Runner is an abstract class.")

    def get_status(self, subject_id=None, step_id=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")

    def _check_input_files(self, subject_ids):
        subjects_with_missing_inputs = []
        for subject_id in subject_ids:
            analysis = self._study.analyses[subject_id]
            if not analysis.inputs.all_file_exists():
                subject = self._study.subjects[subject_id]
                subjects_with_missing_inputs.append(str(subject))
        if len(subjects_with_missing_inputs) != 0:
            raise MissingInputFileError("Subjects: %s" % ", ".join(subjects_with_missing_inputs))

 
class MissingInputFileError(Exception):
    pass

    
class ThreadRunner(Runner):
    
    def __init__(self, study):
        super(ThreadRunner, self).__init__(study)
        
        self._execution_thread = threading.Thread(name = "analysis run",
                                                  target = ThreadRunner._sync_run,
                                                  args =([self]))
        self._lock = threading.RLock()
        self._interruption = False
        self._last_run_failed = False

    def _sync_run(self):
        self._last_run_failed = False
        command_list = []
        for analysis in self._study.analyses.values():
            command_list.extend(analysis.get_command_list())
        for command in command_list:
            with self._lock:
                if self._interruption:
                    self._interruption = False
                    break
            command_to_run = ""
            for arg in command:
                command_to_run += "\"%s\" " % arg
            print "\nrun: " + repr(command_to_run)
            return_value = os.system(command_to_run)
            if return_value != 0:
                self._last_run_failed = True
                break

    def run(self, subject_ids=ALL_SUBJECTS):
        self._check_input_files()
        if not self._execution_thread.is_alive():
            self._execution_thread.setDaemon(True)
            self._execution_thread.start()
    
    def is_running(self, subject_id=None, step_id=None, update_status=True):
        _ = subject_id
        _ = step_id
        return self._execution_thread.is_alive() 
    
    def wait(self, subject_id=None, step_id=None):
        _ = subject_id
        _ = step_id
        self._execution_thread.join()
        
    def has_failed(self, subject_id=None, step_id=None):
        _ = subject_id
        _ = step_id
        return self._last_run_failed

    def stop(self, subject_id=None, step_id=None):
        _ = subject_id
        _ = step_id
        with self._lock:
            self._interruption = True
        self._execution_thread.join()
        with self._lock:
            if self._interruption:
                # the thread ended without being interrupted
                self._interruption = False
            else:
                self._study.clear_results()
            
              
class  SomaWorkflowRunner(Runner):
    WORKFLOW_NAME_SUFFIX = "Morphologist user friendly analysis"
    
    def __init__(self, study):
        super(SomaWorkflowRunner, self).__init__(study)
        self._workflow_controller = WorkflowController()
        self._init_internal_parameters()
        self._delete_old_workflows()

    def _init_internal_parameters(self):
        self._workflow_id = None
        self._jobid_to_step = {} # subjectid -> (job_id -> step)
        self._cached_jobs_status = None

    def _delete_old_workflows(self):        
        for (workflow_id, (name, _)) in self._workflow_controller.workflows().iteritems():
            if name is not None and name.endswith(self.WORKFLOW_NAME_SUFFIX):
                self._workflow_controller.delete_workflow(workflow_id)
          
    def run(self, subject_ids=ALL_SUBJECTS):
        self._init_internal_parameters()
        cpus_number = self._cpus_number()
        self._workflow_controller.scheduler_config.set_proc_nb(cpus_number)
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self._study.subjects
        self._check_input_files(subject_ids)
        workflow = self._create_workflow(subject_ids)
        if self._workflow_id is not None:
            self._workflow_controller.delete_workflow(self._workflow_id)
        self._workflow_id = self._workflow_controller.submit_workflow(workflow, name=workflow.name)
        self._build_jobid_to_step()
        # the status does not change immediately after run, 
        # so we wait for the status WORKFLOW_IN_PROGRESS or timeout
        status = self._workflow_controller.workflow_status(self._workflow_id)
        try_count = 8
        while ((status != sw.constants.WORKFLOW_IN_PROGRESS) and \
                                                (try_count > 0)):
            time.sleep(0.25)
            status = self._workflow_controller.workflow_status(self._workflow_id)
            try_count -= 1

    def _cpus_number(self):
        cpus_count = multiprocessing.cpu_count()
        cpus_settings = settings.runner.selected_processing_units_n
        if cpus_settings > cpus_count:
            print "Warning: bad setting value:\n" + \
                "  (selected_processing_units_n=%d) " % cpus_settings + \
                "> number of available processing units: %d" % cpus_count
            cpus_number = min(cpus_settings, cpus_count)
        else:
            cpus_number = cpus_settings
        return cpus_number

    def _create_workflow(self, subject_ids):
        jobs = []
        dependencies = []
        groups = []
        
        for subject_id in subject_ids:
            analysis = self._study.analyses[subject_id]
            subject = self._study.subjects[subject_id]
            subject_jobs = []
            previous_job = None
            
            for command, step_id in analysis.remaining_commands_to_run():
                job = Job(command=command, name=step_id)
                job.user_storage = step_id
                subject_jobs.append(job)
                if previous_job is not None:
                    dependencies.append((previous_job, job))
                previous_job = job

            # skip finished analysis
            if len(subject_jobs) != 0:
                group = Group(name=str(subject), elements=subject_jobs)
                group.user_storage = subject_id
                groups.append(group)
            jobs.extend(subject_jobs)
        
        workflow = Workflow(jobs=jobs, dependencies=dependencies, 
                            name=self._define_workflow_name(),
                            root_group=groups)
        return workflow

    def _build_jobid_to_step(self):
        self._jobid_to_step = {}
        workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in workflow.groups:
            subjectid = group.user_storage
            self._jobid_to_step[subjectid] = BidiMap('job_id', 'step_id')
            job_list = group.elements 
            for job in job_list:
                job_id = workflow.job_mapping[job].job_id
                step_id = job.user_storage
                self._jobid_to_step[subjectid][job_id] = step_id

    def _define_workflow_name(self): 
        return self._study.name + " " + self.WORKFLOW_NAME_SUFFIX
            
    def is_running(self, subject_id=None, step_id=None, update_status=True):
        status = self.get_status(subject_id, step_id, update_status)
        return status == Runner.RUNNING

    def get_running_step_ids(self, subject_id, update_status=True):
        if update_status:
            self._update_jobs_status()
        running_step_ids = self._get_subject_filtered_step_ids(subject_id, Runner.RUNNING)
        return running_step_ids
                    
    def wait(self, subject_id=None, step_id=None):
        if subject_id is None and step_id is None:
            Helper.wait_workflow(self._workflow_id, self._workflow_controller)
        elif subject_id is not None:
            if step_id is None:
                raise NotImplementedError
            else:
                self._step_wait(subject_id, step_id)
        else:
            raise NotImplementedError

    def _step_wait(self, subject_id, step_id):
        job_id = self._jobid_to_step[subject_id][step_id, 'step_id']
        self._workflow_controller.wait_job([job_id])
        
    def has_failed(self, subject_id=None, step_id=None, update_status=True):
        status = self.get_status(subject_id, step_id, update_status)
        return status == Runner.FAILED

    def get_failed_step_ids(self, subject_id, update_status=True):
        if update_status:
            self._update_jobs_status()
        failed_step_ids = self._get_subject_filtered_step_ids(subject_id, Runner.FAILED)
        return failed_step_ids

    def stop(self, subject_id=None, step_id=None):
        if not self.is_running():
            raise RuntimeError("Runner is not running.")
        if subject_id is None and step_id is None:
            self._workflow_stop()
        elif subject_id is not None:
            if step_id is None:
                raise NotImplementedError
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def _workflow_stop(self):
        self._workflow_controller.stop_workflow(self._workflow_id)
        interrupted_step_ids = self._get_filtered_step_ids(Runner.INTERRUPTED)
        for subject_id, step_ids in interrupted_step_ids.iteritems():
            analysis = self._study.analyses[subject_id]
            analysis.clear_results(step_ids)

    def _get_filtered_step_ids(self, status, update_status = True):
        if update_status:
            self._update_jobs_status()
        filtered_step_ids_by_subject_id = {}
        for subject_id in self._jobid_to_step:
            filtered_step_ids = self._get_subject_filtered_step_ids(subject_id, status)
            filtered_step_ids_by_subject_id[subject_id] = filtered_step_ids
        return filtered_step_ids_by_subject_id       
             
    def _get_subject_filtered_step_ids(self, subject_id, status):
        step_ids = []
        subject_jobs = self._get_subject_jobs(subject_id)
        jobs_status=self._get_jobs_status(update_status=False)
        for job_id in subject_jobs:
            job_status = jobs_status[job_id]
            if job_status & status:
                step_ids.append(subject_jobs[job_id])
        return step_ids
           
    def get_status(self, subject_id=None, step_id=None, update_status=True):
        if self._workflow_id is None:
            status = Runner.NOT_STARTED
        elif subject_id is None and step_id is None:
            if update_status:
                self._update_jobs_status()
            status = self._get_workflow_status()
        elif subject_id is not None and step_id is None:
            status = self._get_subject_status(subject_id, update_status)
        else:
            status = self._get_step_status(subject_id, step_id, update_status)
        return status
               
    def _get_workflow_status(self):
        sw_status = self._workflow_controller.workflow_status(self._workflow_id)
        if (sw_status in [sw.constants.WORKFLOW_IN_PROGRESS, sw.constants.WORKFLOW_NOT_STARTED]):
            status = Runner.RUNNING
        else:
            has_failed = (len(Helper.list_failed_jobs(self._workflow_id, 
                                                      self._workflow_controller, 
                                                      include_aborted_jobs=True, 
                                                      include_user_killed_jobs=True)) != 0)
            if has_failed:
                status = Runner.FAILED
            else:
                status = Runner.SUCCESS
        return status
    
    def _get_subject_status(self, subject_id, update_status=True):
        status = Runner.NOT_STARTED
        subject_jobs = self._get_subject_jobs(subject_id)
        if subject_jobs:
            jobs_status=self._get_jobs_status(update_status)
            status = Runner.SUCCESS
            for job_id in subject_jobs:
                job_status = jobs_status[job_id]
                # XXX hypothesis: the workflow is linear for a subject (no branch)
                if job_status & (Runner.RUNNING | Runner.INTERRUPTED):
                    status = job_status
                    break
                elif job_status & Runner.UNKNOWN:
                    status = job_status
        return status
        
    def _get_step_status(self, subject_id, step_id, update_status=True):
        status = Runner.NOT_STARTED
        subject_jobs = self._get_subject_jobs(subject_id)
        if subject_jobs:
            job_id = subject_jobs[step_id, "step_id"]
            jobs_status = self._get_jobs_status(update_status)
            status = jobs_status[job_id]       
        return status
    
    def _get_subject_jobs(self, subject_id):
        return self._jobid_to_step.get(subject_id, [])
        
    def _get_jobs_status(self, update_status=True):
        if update_status or self._cached_jobs_status is None:
            self._update_jobs_status()
        return self._cached_jobs_status
        
    def _update_jobs_status(self):
        jobs_status = {} # job_id -> status
        job_info_seq, _, _, _ = self._workflow_controller.workflow_elements_status(self._workflow_id)
        for job_id, sw_status, _, exit_info, _ in job_info_seq:
            exit_status, exit_value, _, _ = exit_info
            status = self._sw_status_to_runner_status(sw_status, exit_status, exit_value)
            jobs_status[job_id] = status
        self._cached_jobs_status = jobs_status
        
    def _sw_status_to_runner_status(self, sw_status, exit_status, exit_value):
        if sw_status in [sw.constants.FAILED,
                         sw.constants.DELETE_PENDING,
                         sw.constants.KILL_PENDING] or \
            (exit_value is not None and exit_value != 0):
            if exit_status == sw.constants.USER_KILLED:
                status = Runner.STOPPED_BY_USER
            elif exit_status == sw.constants.EXIT_ABORTED:
                status = Runner.NOT_STARTED
            else:
                status = Runner.FAILED
        elif sw_status == sw.constants.DONE:
            status = Runner.SUCCESS
        # XXX status UNDERTERMINED  is supposed to be a transitory status 
        # after or before the running status
        elif sw_status in [sw.constants.RUNNING, sw.constants.QUEUED_ACTIVE, 
                           sw.constants.SUBMISSION_PENDING, sw.constants.UNDETERMINED]:
            status = Runner.RUNNING
        elif sw_status == sw.constants.NOT_SUBMITTED:
            status = Runner.NOT_STARTED
        else: 
            # WARNING, SYSTEM_ON_HOLD, USER_ON_HOLD,
            # USER_SYSTEM_ON_HOLD, SYSTEM_SUSPENDED, USER_SUSPENDED,
            # USER_SYSTEM_SUSPENDED
            status = Runner.UNKNOWN
        return status
