import threading
import os

class Runner(object):
    ''' Abstract class '''
    
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
    
    
class ThreadRunner(Runner):
    
    def __init__(self, study):
        super(ThreadRunner, self).__init__()
        self._study = study
        self._analysis_runners = {}
        for subjectname, analysis in self._study.analysis.items():
            self._analysis_runners[subjectname] = ThreadAnalysisRunner(analysis)

    
    def run(self):
        for subjectname in self._study.list_subject_names():
            print "\nRun the analysis for the subject %s." % subjectname
            runner = self._analysis_runners[subjectname]
            if not runner.is_running():
                runner.run()
    
    def is_running(self):
        running = False
        for subjectname in self._study.list_subject_names():
            if self._analysis_runners[subjectname].is_running():
                running = True
                break
        return running
             
    def wait(self):
        for subjectname in self._study.list_subject_names():
            self._analysis_runners[subjectname].wait()
            
    def last_run_failed(self):
        failed = False
        for subjectname in self._study.list_subject_names():
            if self._analysis_runners[subjectname].last_run_failed():
                failed = True
                break
        return failed

        
    def stop(self):
        for subjectname in self._study.list_subject_names():
            self._analysis_runners[subjectname].stop()
        
        
class ThreadAnalysisRunner(Runner):
    
    def __init__(self, analysis):
        super (ThreadAnalysisRunner, self).__init__()
        self._analysis = analysis
        self._execution_thread = threading.Thread(name = "analysis run",
                                                  target = ThreadAnalysisRunner._sync_run,
                                                  args =([self]))
        self._lock = threading.RLock()
        self._interruption = False
        self._last_run_failed = False
 

    def _sync_run(self):
        self._last_run_failed = False
        command_list = self._analysis.get_command_list()
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
        self._analysis.check_parameter_values_filled()
        self._analysis.check_input_files_exist()
        self._analysis.check_output_files_dont_exist()

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
                self._analysis.clear_output_files()
    
              
class  SWRunner(Runner):
    pass