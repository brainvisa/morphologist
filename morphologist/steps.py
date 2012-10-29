import os

class Step(object):
    ''' Abstract class '''

    def __init__(self):
      pass

    def run(self):
        separator = " "
        to_execute = separator.join(self.get_command())
        print "run the command: \n" + to_execute + "\n"
        os.system(to_execute)
 


class BiasCorrection(Step):
 
    mri = None

    commissure_coordinates = None

    #outputs
    hfiltered = None

    white_ridges = None

    edges = None

    variance = None

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
                   '-Points', self.commissure_coordinates,
                   '-Kregul', "20.0",
                   '-sampling', "16.0",
                   '-Kcrest', "20.0",
                   '-Grid', "2",
                   '-ZregulTuning', "0.5",
                   '-vp', "75",
                   '-e', "3",
                   '-Last', "auto"]                  

        # TODO referentials
        return command
   
 
class HistogramAnalysis(Step):

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

class BrainSegmentation(Step):

    mri_corrected = None

    commissure_coordinates = None

    white_ridges = None

    edges = None

    variance = None

    histo_analysis = None

    erosion_size = None

    # output
    brain_mask = None

    def __init__(self):
        super(BrainSegmentation, self).__init__()
        self.erosion_size = 1.8

    def get_command(self):
        command = ['VipGetBrain',
                   '-berosion', str(self.erosion_size),
                   '-i', self.mri_corrected,
                   '-analyse', 'r', 
                   '-hname',  self.histo_analysis,
                   '-bname', self.brain_mask,
                   '-First', "0",
                   '-Last', "0", 
                   '-layer', "0",
                   '-Points', self.commissure_coordinates,
                   '-m', "V",
                   '-Variancename', self.variance,
                   '-Edgesname', self.edges,
                   '-Ridge', self.white_ridges,
                   ]
        # TODO referentials
        return command

