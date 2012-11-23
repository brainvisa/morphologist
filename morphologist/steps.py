import os

class Step(object):
    ''' Abstract class '''

    def __init__(self):
        pass

    def run(self):
        # WARNING do not overload: get_command should be used to run the step 
        separator = " "
        to_execute = separator.join(self.get_command())
        print "run the command: \n" + to_execute + "\n"
        return os.system(to_execute)

    def get_command(self):
        raise Exception("Step is an abstract class.")


