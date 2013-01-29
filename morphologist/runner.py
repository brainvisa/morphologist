# -*- coding: utf-8 -*-
import threading
import os
import time
from datetime import timedelta, datetime

import soma.workflow as sw

from soma.workflow.client import WorkflowController, Helper, Workflow, Job, Group


import collections


class BidiMap(collections.MutableMapping):
    '''Bi-directional map'''

    def __init__(self, default_keyname='default', reverse_keyname='reverse'):
        super(BidiMap, self).__init__()
        self._map = {}
        self._rmap = {}
        self.default_keyname = default_keyname
        self.reverse_keyname = reverse_keyname
        self.iter_keyname = default_keyname

    def __len__(self):
        return len(self._map)

    def __delitem__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        del first_map[key]
        keys = [k for k, v in snd_map.items() if v == key]
        for k in keys: del snd_map[k]

    def __getitem__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        return first_map[key]

    def __setitem__(self, key_keyname, value):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        first_map[key] = value
        snd_map[value] = key

    def __contains__(self, key_keyname):
        key, keyname = self._get_key_keyname(key_keyname)
        first_map, snd_map = self._select_maps(keyname)
        return first_map.__contains__(key)
        
    def __iter__(self):
        first_map, snd_map = self._select_maps(self.iter_keyname)
        for key in first_map:
            yield key

    def _select_maps(self, keyname):
        if keyname is None or keyname == self.default_keyname:
            first_map = self._map
            snd_map = self._rmap
        elif keyname == self.reverse_keyname:
            first_map = self._rmap
            snd_map = self._map
        else:
            raise KeyError(keyname)
        return first_map, snd_map

    def _get_key_keyname(self, key_keyname):
        if isinstance(key_keyname, tuple):
            key, keyname = key_keyname
        else:
            key, keyname = key_keyname, None
        if keyname is None:
            keyname = self.default_keyname
        return key, keyname

    def __str__(self):
        s = "('%s': %s, " % (self.default_keyname, self._map)
        s += "'%s': %s)" % (self.reverse_keyname, self._rmap)
        return s
        

class Runner(object):
    ''' Abstract class '''
    FAILED = 'failed'
    SUCCESS = 'success'
    NOT_STARTED = 'not started'
    RUNNING = 'running'
    
    def __init__(self, study):
        super(Runner, self).__init__()
        self._study = study

    def run(self):
        raise NotImplementedError("Runner is an abstract class.")
    
    def is_runnning(self, subject_name=None):
        raise NotImplementedError("Runner is an abstract class.")
    
    def wait(self):
        raise NotImplementedError("Runner is an abstract class.")

    def wait_step(self, subjectname, stepname):
        raise NotImplementedError("Runner is an abstract class.")
        
    def last_run_failed(self):
        raise NotImplementedError("Runner is an abstract class.")

    def failed_steps(self):
        raise NotImplementedError("Runner is an abstract class.")

    def failed_steps_for_subject(self, subjectname):
        raise NotImplementedError("Runner is an abstract class.")

    def step_has_failed(self, subjectname, stepname):
        raise NotImplementedError("Runner is an abstract class.")

    def stop(self):
        raise NotImplementedError("Runner is an abstract class.")

    def steps_status(self):
        raise NotImplementedError("Runner is an abstract class.")

    def _check_input_output_files(self):
        self._check_input_files()
        self._check_output_files()

    def _check_input_files(self):
        subjects_with_missing_inputs = []
        for subjectname, analysis in self._study.analyses.iteritems():
            if len(analysis.inputs.list_missing_files()) != 0:
                subjects_with_missing_inputs.append(subjectname)
        if len(subjects_with_missing_inputs) != 0:
            raise MissingInputFileError("Subjects: %s" % ", ".join(subjects_with_missing_inputs))

    def _check_output_files(self):
        subjects_with_existing_outputs = []
        for subjectname, analysis in self._study.analyses.iteritems():
            if len(analysis.outputs.list_existing_files()) != 0:
                subjects_with_existing_outputs.append(subjectname)
        if len(subjects_with_existing_outputs) != 0:
            raise OutputFileExistError("Subjects: %s" % ", ".join(subjects_with_existing_outputs))
        
 
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
                self._study.clear_results()
            
              
class  SomaWorkflowRunner(Runner):
    WORKFLOW_NAME_SUFFIX = "Morphologist user friendly analysis"
    
    def __init__(self, study):
        super(SomaWorkflowRunner, self).__init__(study)
        self._workflow_controller = WorkflowController()
        self._reset_internal_parameters()
        self._delete_old_workflows()
        cpu_count = Helper.cpu_count()
        if cpu_count > 1:
            cpu_count -= 1
        self._workflow_controller.scheduler_config.set_proc_nb(cpu_count)

    def _reset_internal_parameters(self):
        self._workflow_id = None
        self._subjects_jobs = None  #subject_name -> list of job_ids
        self._jobs_status = None # job_id -> status
        self._last_status_update = None
        self._jobid_to_step = {} # subject_name -> (job_id -> step)
        self._failed_jobs = None
        
    def _delete_old_workflows(self):        
        for (workflow_id, (name, _)) in self._workflow_controller.workflows().iteritems():
            if name is not None and name.endswith(self.WORKFLOW_NAME_SUFFIX):
                self._workflow_controller.delete_workflow(workflow_id)
          
    def run(self):
        self._reset_internal_parameters()
        self._check_input_output_files()
        workflow = self._create_workflow()
        if self._workflow_id is not None:
            self._workflow_controller.delete_workflow(self._workflow_id)
        self._workflow_id = self._workflow_controller.submit_workflow(workflow, name=workflow.name)
        self._update_jobid_to_step()
        self._update_subjects_jobs()
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
        
        for subjectname, analysis in self._study.analyses.iteritems():
            subject_jobs=[]
            previous_job=None
            
            analysis.propagate_parameters() # FIXME : needed ?
            for step in analysis.steps():
                command = step.get_command()
                job = Job(command=command, name=step.name)
                subject_jobs.append(job)
                if previous_job is not None:
                    dependencies.append((previous_job, job))
                previous_job = job
                
            group = Group(name=subjectname, elements=subject_jobs)
            groups.append(group)
            jobs.extend(subject_jobs)
        
        workflow = Workflow(jobs=jobs, dependencies=dependencies, 
                            name=self._define_workflow_name(),
                            root_group=groups)
        return workflow

    def _update_jobid_to_step(self):
        self._jobid_to_step = {}
        workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in workflow.groups:
            subjectname = group.name
            self._jobid_to_step[subjectname] = BidiMap('job_id', 'stepname')
            job_list = group.elements 
            for job in job_list:
                job_id = workflow.job_mapping[job].job_id
                stepname = job.name
                self._jobid_to_step[subjectname][job_id] = stepname

    def _update_subjects_jobs(self): # TODO: can be replaced/removed (see above)
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

    def _define_workflow_name(self): 
        return self._study.name + " " + self.WORKFLOW_NAME_SUFFIX
            
    def is_running(self, subject_name=None):
        running = False
        if self._workflow_id is not None:
            if subject_name:
                running = self._subject_is_running(subject_name)
            else:
                status = self._workflow_controller.workflow_status(self._workflow_id)
                running = (status == sw.constants.WORKFLOW_IN_PROGRESS)
        return running
    
    def _subject_is_running(self, subject_name):
        if self._jobs_status == None or \
            datetime.now() - self._last_status_update > timedelta(seconds=2):
            self._update_jobs_status()
            self._last_status_update = datetime.now()
        running = False
        for job_id in self._subjects_jobs[subject_name]:
            if self._jobs_status[job_id] == Runner.RUNNING:
                running = True
                break
        return running
            
    def _update_jobs_status(self):
        self._jobs_status = {}
        job_info_seq, _, _, _ = self._workflow_controller.workflow_elements_status(self._workflow_id)
        for job_id, sw_status, _, _, _ in job_info_seq:
            status = self._sw_status_to_runner_status(sw_status)
            self._jobs_status[job_id] = status

    def _sw_status_to_runner_status(self, sw_status):
        if sw_status in [sw.constants.FAILED,
                         sw.constants.DELETE_PENDING,
                         sw.constants.KILL_PENDING]:
            status = Runner.FAILED
        elif sw_status == sw.constants.DONE:
            status = Runner.SUCCESS # FIXME : missing exit value = 0
        elif sw_status == sw.constants.NOT_SUBMITTED:
            status = Runner.NOT_STARTED
        elif not sw_status in [sw.constants.WARNING]:
            status = Runner.RUNNING
        return status
            
    def _job_is_running(self, status):
        return not status in [sw.constants.NOT_SUBMITTED,
                              sw.constants.DONE,
                              sw.constants.FAILED,
                              sw.constants.DELETE_PENDING,
                              sw.constants.KILL_PENDING,
                              sw.constants.WARNING]

    def wait(self):
        Helper.wait_workflow(self._workflow_id, self._workflow_controller)

    def wait_step(self, subjectname, stepname):
        job_id = self._jobid_to_step[subjectname][stepname, 'stepname']
        self._workflow_controller.wait_job([job_id])
        
    def last_run_failed(self):
        failed = False
        if self._workflow_id is not None:
            failed = (len(Helper.list_failed_jobs(self._workflow_id, 
                                                  self._workflow_controller, 
                                                  include_aborted_jobs=True, 
                                                  include_user_killed_jobs=True)) != 0)
        return failed     

    def failed_steps(self):
        if self.is_running():
            raise RuntimeError("Runner is still running.")
        self._update_failed_jobs_if_needed()
        failed_steps = {}
        for job_data in self._failed_jobs:
            subjectname = job_data.groupname
            stepname = self._jobid_to_step[subjectname][job_data.job_id]
            analysis = self._study.analyses[subjectname]
            step = analysis.step_from_name(stepname)
            failed_steps[subjectname] = step
        return failed_steps

    def failed_steps_for_subject(self, subjectname):
        if self.is_running():
            raise RuntimeError("Runner is still running.")
        self._update_failed_jobs_if_needed()
        failed_steps = []
        for job_data in self._failed_jobs:
            if subjectname == job_data.groupname:
                stepname = self._jobid_to_step[subjectname][job_data.job_id]
                analysis = self._study.analyses[subjectname]
                step = analysis.step_from_name(stepname)
                failed_steps.append(step)
        return failed_steps

    def step_has_failed(self, subjectname, stepname):
        if self.is_running():
            raise RuntimeError("Runner is still running.")
        self._update_failed_jobs_if_needed()
        failed_steps = []
        for job_data in self._failed_jobs:
            if subjectname == job_data.groupname and \
                stepname == self._jobid_to_step[subjectname][job_data.job_id]:
                return True # if step failed
        return False # if step succeed or was not even started

    def steps_status(self):
        steps_status = {}
        # FIXME : not optimal, muste be done only if needed
        self._update_jobs_status()
        engine_workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in engine_workflow.groups:
            subjectname = group.name
            steps_status[subjectname] = {}
            for job in group.elements:
                job_id = engine_workflow.job_mapping[job].job_id
                stepname = self._jobid_to_step[subjectname][job_id]
                analysis = self._study.analyses[subjectname]
                step = analysis.step_from_name(stepname)
                jobs_status = self._jobs_status[job_id]
                steps_status[subjectname][stepname] = (step, jobs_status)
        return steps_status

    def _update_failed_jobs_if_needed(self):
        if self._failed_jobs is not None:
            return
        exit_info_by_job = self._sw_exit_info_by_job()
        dep_graph = self._sw_dep_graph(exit_info_by_job)
        self._failed_jobs = self._sw_really_failed_jobs_from_dep_graph(dep_graph)

    def stop(self):
        if not self.is_running():
            raise RuntimeError("Runner is not running.")
        self._workflow_controller.stop_workflow(self._workflow_id)
        self._update_jobs_status()
        self._update_failed_jobs_if_needed()
        workflow = self._workflow_controller.workflow(self._workflow_id)
        for job_data in self._failed_jobs:
            subjectname = job_data.groupname
            stepname = self._jobid_to_step[subjectname][job_data.job_id]
            analysis = self._study.analyses[subjectname]
            step = analysis.step_from_name(stepname)
            step.outputs.clear()

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


import collections


class Graph(object):
    '''
    example : (A is the root node)

    A ----> B -----> C <------------·
    |                               |
    ·-----> D -----> E -----·       |
            |               |       |
            ·------> F -----·-----> G
      
    dependencies : [[1, 3],  # A -> (B, D)
                    [2],     # B -> C
                    [],      # C
                    [4, 5],  # D -> (E, F)
                    [6],     # E -> G
                    [6],     # F -> G
                    [2]]     # G -> C
    data = [A, B, C, D, E, F, G]
    '''

    def __init__(self, dependencies=None, data=None):
        if dependencies is not None:
            self._dependencies = dependencies
        if data:
            self._data = data
        else:
            self._data = [None] * len(self)

    @staticmethod
    def from_soma_workflow(workflow):
        '''
    an additionnal root node is added at index 0 with None data
        '''
        class SWGraphData(object):

            def __init__(self, groupname, job_id):
                self.groupname = groupname
                self.job_id = job_id

        def _find_alone_starting_nodes(dependencies):
            marks = [False] * len(dependencies)
            marks[0] = True # special case for root nodes
            for deps in dependencies:
                for dep in deps:
                    marks[dep] = True
            starting_nodes = [i for i, mark in enumerate(marks)
                                            if mark is False]
            return starting_nodes
        size = len(workflow.jobs) + 1 # add root node
        data = [None] * size
        dependencies = [[] for i in range(size)]
        job_map = {}
        ind = 1 # take into account root node
        for group in workflow.groups:
            for job in group.elements:
                job_id = workflow.job_mapping[job].job_id
                job_map[id(job)] = ind
                data[ind] = SWGraphData(group.name, job_id)
                ind += 1
        for src, dst in workflow.dependencies:
            id_src, id_dst = id(src), id(dst)
            dependencies[job_map[id_dst]].append(job_map[id_src])
        # all starting nodes are linked to a spurious root node
        dependencies[0] = _find_alone_starting_nodes(dependencies)
        return Graph(dependencies, data)

    def __len__(self):
        return len(self._dependencies)

    def dependencies(self, node):
        return self._dependencies[node]

    def data(self, node):
        return self._data[node]

    def set_data(self, data):
        assert len(data) == len(self)
        self._data = data

    def __iter__(self):
        for data in self._data:
            yield data

    def breadth_first_coverage(self, func=(lambda n, f : None),
                                     func_extra_data=None):
        marks = [False] * len(self)
        marks[0] = True
        queue = collections.deque([0])
        while len(queue):
            node = queue.popleft()
            continue_graph_coverage = func(self, node, func_extra_data)
            if not continue_graph_coverage: continue # skip dependencies
            for dep in self._dependencies[node]:
                if not marks[dep]:
                    queue.append(dep)
                    marks[dep] = True
