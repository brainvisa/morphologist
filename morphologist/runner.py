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
 
 
class MissingInputFileError(Exception):
    pass

class OutputFileExistError(Exception):
    pass
   
    
class ThreadRunner(Runner):
    
    def __init__(self, study):
        super(ThreadRunner, self).__init__()
        self._study = study
        self._execution_thread = threading.Thread(name = "analysis run",
                                                  target = ThreadRunner._sync_run,
                                                  args =([self]))
        self._lock = threading.RLock()
        self._interruption = False
        self._last_run_failed = False

 
    def _sync_run(self):
        self._last_run_failed = False
        command_list = []
        for analysis in self._study.analysis.values():
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
        subjects_with_missing_inputs = []
        subjects_with_existing_outputs = []
        for subjectname, analysis in self._study.analysis.items():
            if (analysis.input_params.list_missing_files() != []):
                subjects_with_missing_inputs.append( subjectname )
            if analysis.output_params.list_existing_files() != []:
                subjects_with_existing_outputs.append( subjectname )
        if subjects_with_missing_inputs != []:
            raise MissingInputFileError( "Subjects : %s" % ", ".join(subjects_with_missing_inputs) )
        if subjects_with_existing_outputs != []:
            raise OutputFileExistError( "Subjects : %s" % ", ".join(subjects_with_existing_outputs) )
        
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
                for analysis in self._study.analysis.values():
                    analysis.clear_output_files()
            
              
class  SWRunner(Runner):
    pass