import os

class Analysis(object):
    ''' Abstract class '''

    def __init__(self):
      pass

    def run(self):
        separator = " "
        to_execute = separator.join(self.get_command())
        print "run the command: \n" + to_execute + "\n"
        os.system(to_execute)
 


class BiasCorrection(Analysis):
 
    mri = None

    commissure_coordinates = None

    hfiltered = None

    white_ridges = None

    edges = None

    variance = None

    # output
    mri_corrected = None

    def __init__(self):
        super(BiasCorrection, self).__init__()

    def get_command(self):
        command = ['VipT1BiasCorrection', 
                   '-i', self.mri, 
                   '-o', self.mri_corrected, 
                   '-wridge', self.white_ridges, 
                   '-ename', self.edges, 
                   '-vname', self.variance, 
                   '-hname', self.hfiltered, 
                   '-Points', self.commissure_coordinates]
        return command
   

class HistogramAnalysis(Analysis):

    mri_corrected = None

    hfiltered = None

    white_ridges = None

    # output
    histo_analysis = None 

    def __init__(self):
        super(HistogramAnalysis, self).__init__()
    
    def get_command(self):
        command = ['VipHistoAnalysis', 
                   '-i', self.mri_corrected, 
                   '-o', self.histo_analysis, 
                   '-Save', 'y',
                   '-Mask', self.hfiltered,
                   '-Ridge', self.white_ridges,
                   '-mode', 'i']
        return command

class ComputeBrainMask(Analysis):

  pass
