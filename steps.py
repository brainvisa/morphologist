import os.path
import copy

class MissingInputFileError(Exception):
    pass

class OutputFileExistError(Exception):
    pass

class MissingParameterValueError(Exception):
    pass


class Step(object):

    def __init__(self):
        self._in_file_params = []
        self._out_file_params = []
        self._extra_params = []

    def check_in_files(self):
        for in_file_param in self._in_file_params:
            in_file_name = getattr(self, in_file_param)
            if not os.path.isfile(in_file_name):
                raise MissingInputFileError(in_file_param)
      
    def check_out_files(self):
        for out_file_param in self._out_file_params:
            out_file_name = getattr(self, out_file_param)
            if os.path.isfile(out_file_name):
                raise OutputFileExistError

    def check_parameter_filled(self):
        all_the_params = copy.copy(self._in_file_params)
        all_the_params.extend(self._out_file_params)
        all_the_params.extend(self._extra_params)
        for param in all_the_params:
            param_value = getattr(self, param)
            if param_value == None:
                raise MissingParameterValueError(param)


    def run(self):
        self.check_parameter_filled()
        self.check_in_files() 
        self.check_out_files()
        for out_file_param in self._out_file_params:
            out_file_name = getattr(self, out_file_param)
            out_file = open(out_file_name, "w")
            out_file.close()
  

class Step1(Step):
    
    def __init__(self):
        super(Step1, self).__init__()
        self.param_in = None
        self.param_out = None
       
        self._in_file_params = ["param_in"]
        self._out_file_params = ["param_out"]
        

class Step2(Step):

    def __init__(self):
        super(Step2, self).__init__()
        self.param_in_1 = None
        self.param_in_2 = None
        self.param_in_3 = None
        self.param_out = None

        self._in_file_params = ["param_in_1", "param_in_2"]  
        self._out_file_params= ["param_out"]
        self._extra_params = ["param_in_3"]
   

class Step3(Step):

    def __init__(self):
        super(Step3, self).__init__()
        self.param_in_1 = None
        self.param_in_2 = None
        self.param_out = None

        self._in_file_params = ["param_in_1", "param_in_2"]  
        self._out_file_params= ["param_out"]


class IntraAnalysis(object):

    def __init__(self):
        super(IntraAnalysis, self).__init__()
        
        self.param_in_1 = None
        self.param_in_2 = None
        self.param_in_3 = None       
        self.param_in_4 = None       
        self.param_out_1 = None
        self.param_out_2 = None
        self.param_out_3 = None

        self.step1 = Step1()
        self.step2 = Step2()
        self.step3 = Step3()

    def run(self):
        self.step1.param_in = self.param_in_1
        self.step1.param_out = self.param_out_1
        self.step2.param_in_1 = self.param_in_2
        self.step2.param_in_2 = self.param_out_1 
        self.step2.param_in_3 = self.param_in_3
        self.step2.param_out = self.param_out_2
        self.step3.param_in_1 = self.param_in_4
        self.step3.param_in_2 = self.param_out_2
        self.step3.param_out = self.param_out_3
        self.step1.run()
        self.step2.run()
        self.step3.run()





