import os

from m_api import BiasCorrection, HistogramAnalysis

def test_bias_correction():
    bias_correction = BiasCorrection()

    base_directory = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition"

    bias_correction.mri = os.path.join(base_directory, "icbm100T.ima") 
    bias_correction.commissure_coordinates = os.path.join(base_directory, "icbm100T.APC") 
    bias_correction.hfiltered = os.path.join(base_directory, "default_analysis/hfiltered_icbm100T.ima")
    bias_correction.white_ridges = os.path.join(base_directory, "default_analysis/whiteridge_icbm100T.ima")
    bias_correction.edges = os.path.join(base_directory, "default_analysis/edges_icbm100T.ima")
    bias_correction.mri_corrected = os.path.join(base_directory, "default_analysis/nobias_icbm100T.ima")
    bias_correction.variance = os.path.join(base_directory, "default_analysis/variance_icbm100T.ima")
    bias_correction.run()

def test_histogram_analysis():
    histo_analysis = HistogramAnalysis()
    
    histo_analysis.mri_corrected = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition/default_analysis/nobias_icbm100T.ima"   
    histo_analysis.histo_analysis = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition/default_analysis/nobias_icbm100T.han"
    histo_analysis.hfiltered = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition/default_analysis/hfiltered_icbm100T.ima"
    histo_analysis.white_ridges = "/volatile/laguitton/data/icbm/icbm/icbm100T/t1mri/default_acquisition/default_analysis/whiteridge_icbm100T.ima"

    histo_analysis.run()


if __name__ == '__main__':

   test_histogram_analysis() 
   test_bias_correction() 
