import os

class Step(object):
    ''' Abstract class '''

    def __init__(self):
        pass

    def run(self):
        # WARNING do not overload: get_command should be used to run the step 
        to_execute = ""
        for arg in self.get_command():
            to_execute += "\"%s\" " % arg
        print "run the command: \n" + to_execute + "\n"
        return os.system(to_execute)

    def get_command(self):
        raise NotImplementedError("Step is an abstract class.")

