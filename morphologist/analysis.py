


class Analysis(object):
     

    def __init__(self):
        self._is_running = False

    def run(self):
        self._is_running = True

    def stop(self):
        self._is_running = False

    def is_running(self):
        return self._is_running

      
class MockAnalysis(Analysis):
    pass 
   
 
#    def __init__(self):
#        pass
#
#    def run(self):
#        pass
#
#    def stop(self):
#        pass
#
#    def is_running(self):
#        pass
#    
     
