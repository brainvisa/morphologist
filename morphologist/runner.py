import threading
import os
import time

from soma.workflow.client import WorkflowController, Helper, Workflow, Job, Group
from soma.workflow.constants import WORKFLOW_IN_PROGRESS

class Runner(object):
    ''' Abstract class '''
    
    def __init__(self, study):
        super(Runner, self).__init__()
        self._study = study

    def run(self):
        raise Exception("Runner is an abstract class.")
    
    def is_runnning(self):
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
        for subjectname, analysis in self._study.analyses.items():
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
        separator = " " 
        for command in command_list:
            with self._lock:
                if self._interruption:
                    self._interruption = False
                    break
            command_to_run = separator.join(command)
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
    
    
    def is_running(self):
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
            
              
class  SWRunner(Runner):
    """Soma-Workflow runner"""
    
    def __init__(self, study):
        super(SWRunner, self).__init__(study)
        self._workflow_controller = WorkflowController()
        self._workflow_id = None
        
    def create_workflow(self):
        jobs = []
        dependencies = []
        groups = []
        
        for subjectname, analysis in self._study.analyses.items():
            subject_jobs=[]
            previous_job=None
            
            for command in analysis.get_command_list():
                job = Job(command = command)
                subject_jobs.append(job)
                if previous_job is not None:
                    dependencies.append((previous_job, job))
                previous_job = job
                
            group = Group(name=self._define_group_name(subjectname), elements=subject_jobs)
            groups.append(group)
            jobs.extend(subject_jobs)
        
        workflow = Workflow(jobs=jobs, dependencies=dependencies, 
                            name = self._define_workflow_name(), root_group = groups)
        return workflow
        
    def _define_workflow_name(self): 
        return "%s Morphologist analysis" % self._study.name
        
    def _define_group_name(self, subjectname):
        return "%s analysis" % subjectname
    
    def run(self):
        self._check_input_output_files()
        workflow = self.create_workflow()
        self._workflow_id = self._workflow_controller.submit_workflow(workflow)
        # FIXME: the status does not change immediately after run
        time.sleep(2)
    
    def is_running(self):
        running = False
        if self._workflow_id is not None:
            status = self._workflow_controller.workflow_status(self._workflow_id)
            running = (status == WORKFLOW_IN_PROGRESS)
        return running
    
    def wait(self):
        Helper.wait_workflow(self._workflow_id, self._workflow_controller)
        
    def last_run_failed(self):
        return Helper.list_failed_jobs(self._workflow_id, self._workflow_controller, 
                                       include_aborted_jobs=True, include_user_killed_jobs=True)
        
    def stop(self):
        if self.is_running():
            self._workflow_controller.stop_workflow(self._workflow_id)
            self._clear_output_files()
