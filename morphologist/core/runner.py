# -*- coding: utf-8 -*-
import os
import time
import threading
import multiprocessing

import soma_workflow as sw
from soma_workflow.client import WorkflowController, Helper, Workflow, Job, Group
from soma_workflow import configuration as swconf

from capsul.pipeline import pipeline_workflow
from capsul.pipeline import pipeline_tools

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

    def set_study(self, study):
        self._study = study

 
class MissingInputFileError(Exception):
    pass



class  SomaWorkflowRunner(Runner):
    WORKFLOW_NAME_SUFFIX = "Morphologist user friendly analysis"

    def __init__(self, study):
        super(SomaWorkflowRunner, self).__init__(study)

        self._workflow_controller = None
        self._init_internal_parameters()

    def get_soma_workflow_credentials(self):
        resource_id = self._study.somaworkflow_computing_resource

        config_file_path = swconf.Configuration.search_config_path()
        resource_list = swconf.Configuration.get_configured_resources(
            config_file_path)
        login_list = swconf.Configuration.get_logins(config_file_path)
        login = None
        if login_list.has_key(resource_id):
            login = login_list[resource_id]

        password = None
        rsa_key_pass = None

        return resource_id, login, password, rsa_key_pass

    def _init_internal_parameters(self):
        self._workflow_id = None
        self._jobid_to_step = {} # subjectid -> (job_id -> step)
        self._cached_jobs_status = None

    def resource_id(self):
        if self._workflow_controller is None:
            resource_id = None
        else:
            resource_id = self._workflow_controller._resource_id
        return resource_id

    def update_controller(self):
        resource_id = self._study.somaworkflow_computing_resource
        if resource_id != self.resource_id():
            self._setup_soma_workflow_controller(create_new=True)

    def set_study(self, study):
        super(SomaWorkflowRunner, self).set_study(study)
        self.update_controller()

    def _setup_soma_workflow_controller(self, create_new=False):
        resource_id, login, password, rsa_key_pass \
            = self.get_soma_workflow_credentials()
        config_file_path = swconf.Configuration.search_config_path()
        try:
            sw_config = swconf.Configuration.load_from_file(
                resource_id, config_file_path)
        except swconf.ConfigurationError:
            sw_config = None
            resource_id = None
        if self._workflow_controller is None or create_new:
            self._workflow_controller = WorkflowController(
                resource_id, login, password=None, config=sw_config,
                rsa_key_pass=None)
            self._delete_old_workflows()

    def _delete_old_workflows(self):
        for (workflow_id, (name, _)) \
                in self._workflow_controller.workflows().iteritems():
            if name is not None and name.endswith(self.WORKFLOW_NAME_SUFFIX):
                self._workflow_controller.delete_workflow(workflow_id)

    def run(self, subject_ids=ALL_SUBJECTS):
        self._setup_soma_workflow_controller()
        self._init_internal_parameters()
        if self._workflow_controller.scheduler_config:
            # in local mode only
            cpus_number = self._cpus_number()
            self._workflow_controller.scheduler_config.set_proc_nb(cpus_number)
        if subject_ids == ALL_SUBJECTS:
            subject_ids = self._study.subjects
        # setup shared path in study_config
        study_config = self._study
        swf_resource = study_config.somaworkflow_computing_resource
        if not hasattr(study_config.somaworkflow_computing_resources_config,
                       swf_resource):
            setattr(study_config.somaworkflow_computing_resources_config,
                    swf_resource, {})
        resource_conf = getattr(
            study_config.somaworkflow_computing_resources_config, swf_resource)
        path_translations = resource_conf.path_translations
        setattr(path_translations, study_config.shared_directory,
                ['brainvisa', 'de25977f-abf5-9f1c-4384-2585338cd7af'])

        #self._check_input_files(subject_ids)
        workflow = self._create_workflow(subject_ids)
        jobs = [j for j in workflow.jobs if isinstance(j, Job)]
        if self._workflow_id is not None:
            self._workflow_controller.delete_workflow(self._workflow_id)
        if len(jobs) == 0:
            # empty workflow: nothing to do
            self._workflow_id = None
            return
        self._workflow_id = self._workflow_controller.submit_workflow(
            workflow, name=workflow.name)
        self._build_jobid_to_step()
        # the status does not change immediately after run, 
        # so we wait for the status WORKFLOW_IN_PROGRESS or timeout
        status = self._workflow_controller.workflow_status(self._workflow_id)
        try_count = 8
        while ((status != sw.constants.WORKFLOW_IN_PROGRESS) and \
                                                (try_count > 0)):
            time.sleep(0.25)
            status = self._workflow_controller.workflow_status(
                self._workflow_id)
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
        study_config = self._study
        workflow = Workflow(
            name='Morphologist UI - %s' % study_config.study_name,
            jobs=[])
        workflow.root_group = []
        initial_vol_format = study_config.volumes_format

        priority = (len(subject_ids) - 1) * 100
        for subject_id in subject_ids:
            analysis = self._study.analyses[subject_id]
            subject = self._study.subjects[subject_id]

            analysis.set_parameters(subject)
            pipeline = analysis.pipeline.process
            pipeline.enable_all_pipeline_steps()
            pipeline_tools.disable_runtime_steps_with_existing_outputs(
                pipeline)

            missing = pipeline_tools.nodes_with_missing_inputs(pipeline)
            if missing:
                print 'MISSING INPUTS IN NODES:', missing
                raise MissingInputFileError("subject: %s" % subject_id)

            wf = pipeline_workflow.workflow_from_pipeline(
                pipeline, study_config=study_config,
                jobs_priority=priority)
            njobs = len([j for j in wf.jobs if isinstance(j, Job)])
            if njobs != 0:
                priority -= 100
                workflow.jobs += wf.jobs
                workflow.dependencies += wf.dependencies
                group = Group(wf.root_group,
                            name='Morphologist %s' % str(subject))
                group.user_storage = subject_id
                workflow.root_group.append(group) # += wf.root_group
                workflow.groups += [group] + wf.groups

        return workflow

    def _build_jobid_to_step(self):
        self._jobid_to_step = {}
        workflow = self._workflow_controller.workflow(self._workflow_id)
        for group in workflow.groups:
            subjectid = group.user_storage
            if subjectid:
                self._jobid_to_step[subjectid] = BidiMap(
                    'job_id', 'step_id')
                job_list = list(group.elements)
                while job_list:
                    job = job_list.pop(0)
                    if isinstance(job, Group):
                        job_list += job.elements
                    else:
                        job_att = workflow.job_mapping.get(job)
                        if job_att:
                            job_id = job_att.job_id
                            step_id = job.user_storage or job.name
                            self._jobid_to_step[subjectid][job_id] = step_id
                        else:
                            print 'job without mapping, subject: %s, job: %s' \
                                % (subjectid, job.name)

    def _define_workflow_name(self): 
        return self._study.name + " " + self.WORKFLOW_NAME_SUFFIX

    def is_running(self, subject_id=None, step_id=None, update_status=True):
        status = self.get_status(subject_id, step_id, update_status)
        return status == Runner.RUNNING

    def get_running_step_ids(self, subject_id, update_status=True):
        if update_status:
            self._update_jobs_status()
        running_step_ids = self._get_subject_filtered_step_ids(
            subject_id, Runner.RUNNING)
        return running_step_ids

    def wait(self, subject_id=None, step_id=None):
        if subject_id is None and step_id is None:
            Helper.wait_workflow(
                self._workflow_id, self._workflow_controller)
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
        failed_step_ids = self._get_subject_filtered_step_ids(
            subject_id, Runner.FAILED)
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
            if step_ids:
                analysis = self._study.analyses[subject_id]
                analysis.clear_results(step_ids)

    def _get_filtered_step_ids(self, status, update_status = True):
        if update_status:
            self._update_jobs_status()
        filtered_step_ids_by_subject_id = {}
        for subject_id in self._jobid_to_step:
            filtered_step_ids = self._get_subject_filtered_step_ids(
                subject_id, status)
            filtered_step_ids_by_subject_id[subject_id] = filtered_step_ids
        return filtered_step_ids_by_subject_id

    def _get_subject_filtered_step_ids(self, subject_id, status):
        step_ids = set()
        subject_jobs = self._get_subject_jobs(subject_id)
        jobs_status = self._get_jobs_status(update_status=False)
        for job_id in subject_jobs:
            job_status = jobs_status[job_id]
            if job_status & status:
                step_ids.add(subject_jobs[job_id])
        return list(step_ids)

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
        if (sw_status in [sw.constants.WORKFLOW_IN_PROGRESS,
                          sw.constants.WORKFLOW_NOT_STARTED]):
            status = Runner.RUNNING
        else:
            has_failed = (len(Helper.list_failed_jobs(
                self._workflow_id, self._workflow_controller,
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
        job_info_seq = self._workflow_controller.workflow_elements_status(
            self._workflow_id)[0]
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
