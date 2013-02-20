# -*- coding: utf-8 -*-
import os
import time
import threading

import soma.workflow as sw
from soma.workflow.client import WorkflowController, Helper, Workflow, Job, Group

from morphologist.core.utils import BidiMap, Graph


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
    NOT_STARTED = 'not started'
    FAILED = 'failed'
    SUCCESS = 'success'
    RUNNING = 'running'
    UNKNOWN = 'unknown'
    
    def __init__(self, study):
        super(Runner, self).__init__()
        self._study = study

    def run(self):
        raise NotImplementedError("Runner is an abstract class.")
    
    def is_running(self, subject=None, stepname=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")
    
    def wait(self, subject=None, stepname=None):
        raise NotImplementedError("Runner is an abstract class.")
    
    def has_failed(self, subject=None, stepname=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")

    def stop(self, subject=None, stepname=None):
        raise NotImplementedError("Runner is an abstract class.")

    def get_status(self, subject=None, stepname=None, update_status=True):
        raise NotImplementedError("Runner is an abstract class.")
    
    def get_steps_status(self):
        raise NotImplementedError("Runner is an abstract class.")

    def _check_input_files(self):
        subjects_with_missing_inputs = []

        for subject_id, subject in self._study.subjects.iteritems():
            analysis = self._study.analyses[subject_id]
            if not analysis.inputs.all_file_exists():
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

    def run(self):
        self._check_input_files()
        if not self._execution_thread.is_alive():
            self._execution_thread.setDaemon(True)
            self._execution_thread.start()
    
    def is_running(self, subject=None, stepname=None, update_status=True):
        _ = subject
        _ = stepname
        return self._execution_thread.is_alive() 
    
    def wait(self, subject=None, stepname=None):
        _ = subject
        _ = stepname
        self._execution_thread.join()
        
    def has_failed(self, subject=None, stepname=None):
        _ = subject
        _ = stepname
        return self._last_run_failed

    def stop(self, subject=None, stepname=None):
        _ = subject
        _ = stepname
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
        cpu_count = Helper.cpu_count()
        if cpu_count > 1:
            cpu_count -= 1
        self._workflow_controller.scheduler_config.set_proc_nb(cpu_count)

    def _init_internal_parameters(self):
        self._workflow_id = None
        self._jobid_to_step = {} # subjectid -> (job_id -> step)
        self._cached_jobs_status = None
        
    def _delete_old_workflows(self):        
        for (workflow_id, (name, _)) in self._workflow_controller.workflows().iteritems():
            if name is not None and name.endswith(self.WORKFLOW_NAME_SUFFIX):
                self._workflow_controller.delete_workflow(workflow_id)
          
    def run(self):
        self._init_internal_parameters()
        self._check_input_files()
        workflow = self._create_workflow()
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

    def _create_workflow(self):
        jobs = []
        dependencies = []
        groups = []
        
        for subject_id, subject in self._study.subjects.iteritems():
            analysis = self._study.analyses[subject_id]
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
            self._jobid_to_step[subjectid] = BidiMap('job_id', 'stepname')
            job_list = group.elements 
            for job in job_list:
                job_id = workflow.job_mapping[job].job_id
                step_id = job.user_storage
                self._jobid_to_step[subjectid][job_id] = step_id

    def _define_workflow_name(self): 
        return self._study.name + " " + self.WORKFLOW_NAME_SUFFIX
            
    def is_running(self, subject=None, stepname=None, update_status=True):
        status = self.get_status(subject, stepname, update_status)
        return status == Runner.RUNNING
            
    def wait(self, subject=None, stepname=None):
        if subject is None and stepname is None:
            Helper.wait_workflow(self._workflow_id, self._workflow_controller)
        elif subject is not None:
            if stepname is None:
                raise NotImplementedError
            else:
                self._step_wait(subject.id(), stepname)
        else:
            raise NotImplementedError

    def _step_wait(self, subjectid, stepname):
        job_id = self._jobid_to_step[subjectid][stepname, 'stepname']
        self._workflow_controller.wait_job([job_id])
        
    def has_failed(self, subject=None, stepname=None, update_status=True):
        status = self.get_status(subject, stepname, update_status)
        return status == Runner.FAILED

    def stop(self, subject=None, stepname=None):
        if not self.is_running():
            raise RuntimeError("Runner is not running.")
        if subject is None and stepname is None:
            self._workflow_stop()
        elif subject is not None:
            if stepname is None:
                raise NotImplementedError
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def _workflow_stop(self):
        self._workflow_controller.stop_workflow(self._workflow_id)
        failed_jobs = self._get_failed_jobs()
        failed_jobs_by_subject = {}
        for job_data in failed_jobs:
            subjectid = job_data.groupname
            stepname = self._jobid_to_step[subjectid][job_data.job_id]
            failed_jobs_by_subject.setdefault(subjectid, []).append(stepname)
        for subjectid, stepnames in failed_jobs_by_subject.items():
            analysis = self._study.analyses[subjectid]
            analysis.clear_results(stepnames)

    def get_status(self, subject=None, stepname=None, update_status=True):
        if self._workflow_id is None:
            status = Runner.NOT_STARTED
        elif subject is None and stepname is None:
            if update_status:
                self._update_jobs_status()
            status = self._get_workflow_status()
        elif subject is not None and stepname is None:
            status = self._get_subject_status(subject.id(), update_status)
        else:
            raise NotImplementedError
        return status
    
    def get_steps_status(self):
        steps_status = {}
        jobs_status = self._get_jobs_status()
        engine_workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in engine_workflow.groups:
            subjectid = group.user_storage
            steps_status[subjectid] = {}
            for job in group.elements:
                job_id = engine_workflow.job_mapping[job].job_id
                stepname = self._jobid_to_step[subjectid][job_id]
                analysis = self._study.analyses[subjectid]
                step = analysis.step_from_name(stepname)
                job_status = jobs_status[job_id]
                steps_status[subjectid][stepname] = (step, job_status)
        return steps_status
           
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
    
    def _get_subject_status(self, subjectid, update_status=True):
        status = Runner.NOT_STARTED
        subject_jobs = self._get_subject_jobs(subjectid)
        if subject_jobs:
            jobs_status=self._get_jobs_status(update_status)
            status = Runner.SUCCESS
            for job_id in subject_jobs:
                job_status = jobs_status[job_id] 
                if job_status in [Runner.RUNNING, Runner.FAILED]:
                    status = job_status
                    break
                elif job_status == Runner.UNKNOWN:
                    status = job_status
        return status
        
    def _get_subject_jobs(self, subjectid):
        return self._jobid_to_step.get(subjectid, [])
        
    def _get_jobs_status(self, update_status=True):
        if update_status or self._cached_jobs_status is None:
            self._update_jobs_status()
        return self._cached_jobs_status
        
    def _update_jobs_status(self):
        jobs_status = {} # job_id -> status
        job_info_seq, _, _, _ = self._workflow_controller.workflow_elements_status(self._workflow_id)
        for job_id, sw_status, _, exit_info, _ in job_info_seq:
            exit_status, exit_value, _, _ = exit_info
            status = self._sw_status_to_runner_status(sw_status, exit_value)
            jobs_status[job_id] = status
        self._cached_jobs_status = jobs_status
        
    def _sw_status_to_runner_status(self, sw_status, exit_value):
        if sw_status in [sw.constants.FAILED,
                         sw.constants.DELETE_PENDING,
                         sw.constants.KILL_PENDING] or \
            (exit_value is not None and exit_value != 0):
            status = Runner.FAILED
        elif sw_status == sw.constants.DONE:
            status = Runner.SUCCESS
        elif sw_status in [sw.constants.RUNNING, sw.constants.NOT_SUBMITTED, 
                           sw.constants.QUEUED_ACTIVE, sw.constants.SUBMISSION_PENDING]:
            status = Runner.RUNNING
        elif sw_status in [sw.constants.WARNING, sw.constants.UNDETERMINED]:
            status = Runner.UNKNOWN
        else: 
            # SYSTEM_ON_HOLD, USER_ON_HOLD,
            # USER_SYSTEM_ON_HOLD, SYSTEM_SUSPENDED, USER_SUSPENDED,
            # USER_SYSTEM_SUSPENDED
            status = Runner.UNKNOWN
        return status
            
    def _get_failed_jobs(self):
        exit_info_by_job = self._sw_exit_info_by_job()
        dep_graph = self._sw_dep_graph(exit_info_by_job)
        failed_jobs = self._sw_really_failed_jobs_from_dep_graph(dep_graph)
        return failed_jobs

    def _sw_exit_info_by_job(self):
        exit_info_by_job = {}
        job_info_seq, _, _, _  = self._workflow_controller.workflow_elements_status(self._workflow_id)
        for job_id, status, _, exit_info, _ in job_info_seq: 
            exit_status, exit_value, _, _ = exit_info
            exit_info_by_job[job_id] = (exit_status, exit_value)
        return exit_info_by_job

    def _sw_dep_graph(self, exit_info_by_job):
        workflow = self._workflow_controller.workflow(self._workflow_id)
        dep_graph = Graph.from_soma_workflow(workflow)
        for data in dep_graph:
            if data is None: continue
            exit_status, exit_value = exit_info_by_job[data.job_id]
            data.success = (exit_status == sw.constants.FINISHED_REGULARLY \
                            and exit_value == 0)
        return dep_graph

    @staticmethod
    def _sw_really_failed_jobs_from_dep_graph(dep_graph):
        def func(graph, node, extra_data):
            data = graph.data(node)
            if data is not None and data.success: return False
            deps = graph.dependencies(node)
            continue_graph_coverage = True
            failed_node = True
            for dep in deps:
                data = graph.data(dep)
                if not data.success:
                    failed_node = False
            if failed_node: # skip root node
                if node != 0:
                    data = graph.data(node)
                    extra_data['failed_jobs'].append(data)
                continue_graph_coverage = False
            return continue_graph_coverage
                
        failed_jobs = []
        func_extra_data = {'failed_jobs' : failed_jobs}
        dep_graph.breadth_first_coverage(func, func_extra_data)
        return failed_jobs
