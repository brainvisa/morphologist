import threading
import os
import time
from datetime import timedelta, datetime

from soma.workflow.client import WorkflowController, Helper, Workflow, Job, Group
from soma.workflow.constants import WORKFLOW_IN_PROGRESS 
from soma.workflow.constants import NOT_SUBMITTED, DONE, FAILED, DELETE_PENDING, KILL_PENDING, WARNING

class Runner(object):
    ''' Abstract class '''
    
    def __init__(self, study):
        super(Runner, self).__init__()
        self._study = study

    def run(self):
        raise Exception("Runner is an abstract class.")
    
    def is_runnning(self, subject_name=None):
        raise Exception("Runner is an abstract class.")
    
    def wait(self):
        raise Exception("Runner is an abstract class.")
        
    def last_run_failed(self):
        raise Exception("Runner is an abstract class.")
        
    def stop(self):
        raise Exception("Runner is an abstract class.")

    def _check_input_output_files(self):
        subjects_with_missing_inputs = []
        subjects_with_existing_outputs = []
        for subjectname, analysis in self._study.analyses.iteritems():
            if (analysis.input_params.list_missing_files() != []):
                subjects_with_missing_inputs.append( subjectname )
            if analysis.output_params.list_existing_files() != []:
                subjects_with_existing_outputs.append( subjectname )
        if subjects_with_missing_inputs != []:
            raise MissingInputFileError( "Subjects : %s" % ", ".join(subjects_with_missing_inputs) )
        if subjects_with_existing_outputs != []:
            raise OutputFileExistError( "Subjects : %s" % ", ".join(subjects_with_existing_outputs) )
        
    def _clear_output_files(self):
        for analysis in self._study.analyses.values():
            analysis.clear_output_files()
            

 
class MissingInputFileError(Exception):
    pass

class OutputFileExistError(Exception):
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
            command_list.extend( analysis.get_command_list() )
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
        self._check_input_output_files()
        if not self._execution_thread.is_alive():
            self._execution_thread.setDaemon(True)
            self._execution_thread.start()
    
    
    def is_running(self, subject_name=None):
        return self._execution_thread.is_alive() 
    
             
    def wait(self):
        self._execution_thread.join()
        
            
    def last_run_failed(self):
        return self._last_run_failed

        
    def stop(self):
        with self._lock:
            self._interruption = True
        self._execution_thread.join()
        with self._lock:
            if self._interruption:
                # the thread ended without being interrupted
                self._interruption = False
            else:
                self._clear_output_files()
            
              
class  SomaWorkflowRunner(Runner):
    
    WORKFLOW_NAME_SUFFIX = "Morphologist user friendly analysis"
    
    def __init__(self, study):
        super(SomaWorkflowRunner, self).__init__(study)
        self._workflow_controller = WorkflowController()
        self._workflow_id = None
        self._subjects_jobs = None  #subject_name -> list of job_ids
        self._jobs_status = None #job_id -> status
        self._last_status_update = None
        self._delete_old_workflows()
        cpu_count = Helper.cpu_count()
        if cpu_count > 1:
            cpu_count -= 1
        self._workflow_controller.scheduler_config.set_proc_nb(cpu_count)
        
    def _delete_old_workflows(self):        
        for (workflow_id, (name, _)) in self._workflow_controller.workflows().iteritems():
            if name is not None and name.endswith(self.WORKFLOW_NAME_SUFFIX):
                self._workflow_controller.delete_workflow(workflow_id)


    def create_workflow(self):
        jobs = []
        dependencies = []
        groups = []
        
        for subjectname, analysis in self._study.analyses.iteritems():
            subject_jobs=[]
            previous_job=None
            
            for command in analysis.get_command_list():
                job = Job(command = command)
                subject_jobs.append(job)
                if previous_job is not None:
                    dependencies.append((previous_job, job))
                previous_job = job
                
            group = Group(name=subjectname, elements=subject_jobs)
            groups.append(group)
            jobs.extend(subject_jobs)
        
        workflow = Workflow(jobs=jobs, dependencies=dependencies, 
                            name=self._define_workflow_name(), root_group=groups)
        return workflow
        
    def _define_workflow_name(self): 
        return self._study.name + " " + self.WORKFLOW_NAME_SUFFIX
    
    def run(self):
        self._check_input_output_files()
        workflow = self.create_workflow()
        if self._workflow_id is not None:
            self._workflow_controller.delete_workflow(self._workflow_id)
        self._workflow_id = self._workflow_controller.submit_workflow(workflow, name=workflow.name)
        self._update_subjects_jobs()
        # the status does not change immediately after run, 
        # so we wait for the status WORKFLOW_IN_PROGRESS or timeout
        status = self._workflow_controller.workflow_status(self._workflow_id)
        try_count = 10
        while ((status != WORKFLOW_IN_PROGRESS) and (try_count > 0)):
            time.sleep(0.5)
            status = self._workflow_controller.workflow_status(self._workflow_id)
            try_count -= 1
        
    def _update_subjects_jobs(self):
        self._subjects_jobs = {}
        engine_workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in engine_workflow.groups:
            subject_name = group.name
            job_list = group.elements 
            job_ids = []
            for job in job_list:
                engine_job = engine_workflow.job_mapping[job]
                job_ids.append(engine_job.job_id)
            self._subjects_jobs[subject_name] = job_ids
            
    
    def is_running(self, subject_name=None):
        running = False
        if self._workflow_id is not None:
            if subject_name:
                running = self._subject_is_running(subject_name)
            else:
                status = self._workflow_controller.workflow_status(self._workflow_id)
                running = (status == WORKFLOW_IN_PROGRESS)
        return running
    
    def _subject_is_running(self, subject_name):
        if self._jobs_status == None or datetime.now() - self._last_status_update > timedelta(seconds=2):
            self._update_jobs_status()
            self._last_status_update = datetime.now()
        running = False
        for job_id in self._subjects_jobs[subject_name]:
            if self._job_is_running(self._job_status[job_id]):
                running = True
                break
        return running
            
    def _update_jobs_status(self):
        self._job_status = {}
        workflow_elements_status = self._workflow_controller.workflow_elements_status(self._workflow_id)
        for job_info in workflow_elements_status[0]:
            job_id = job_info[0]
            status = job_info[1]
            self._job_status[job_id] = status
            
    def _job_is_running(self, status):
        return not status in [NOT_SUBMITTED, DONE, FAILED, DELETE_PENDING, KILL_PENDING, WARNING]
            
    
    def wait(self):
        Helper.wait_workflow(self._workflow_id, self._workflow_controller)
        
    def last_run_failed(self):
        failed = False
        if self._workflow_id is not None:
            failed = (len(Helper.list_failed_jobs(self._workflow_id, 
                                                  self._workflow_controller, 
                                                  include_aborted_jobs=True, 
                                                  include_user_killed_jobs=True)) != 0)
        return failed     
        
    def stop(self):
        if self.is_running():
            self._workflow_controller.stop_workflow(self._workflow_id)
            self._clear_output_files()
