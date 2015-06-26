'''
    Takes AnalysisSoftware (https://github.com/BristolTopGroup/AnalysisSoftware) 
    output files and extracts the TTJet normalisation for each measured variable
    by subtracting backgrounds from data.
    
    Usage:
        TBD
        
    TODO: In the end this and 01_get_fit_results.py should be merged.
    All should come down to the function to extract the # events from TTJet
'''
from __future__ import division
from optparse import OptionParser
from tools.ROOT_utils import set_root_defaults
from tools.logger import log
from config import XSectionConfig
from src.cross_section_measurement.lib import closure_tests
from rootpy.io.file import File
from tools.file_utilities import write_data_to_JSON

# define logger for this module
mylog = log["01b_get_ttjet_normalisation"]

class TTJetNormalisation:
    '''
        Determines the normalisation for top quark pair production based on
        different methods. Unless stated otherwise all templates and 
        (initial) normalisations are taken from simulation, except for QCD 
        where the template is extracted from data.
        
        Supported methods:
        BACKGROUND_SUBTRACTION: 
            Subtracts the known backgrounds from data to obtain TTJet template 
            and normalisation
        SIMULTANEOUS_FIT:
            Uses Minuit and several fit variables (quotation needed) to perform
            a simultaneous fit (does not use statistical errors of templates).
        FRACTION_FITTER:
            Uses the TFractionFitter class to fit the TTJet normalisation
    '''
    
    BACKGROUND_SUBTRACTION = 10
    SIMULTANEOUS_FIT = 20
    FRACTION_FITTER = 30
    
    @mylog.trace()
    def __init__( self,
                 config,
                 variable,
                 category = 'central',
                 channel = 'electron',
                 method = BACKGROUND_SUBTRACTION ):
        self.config = config
        self.variable = variable
        self.category = category
        self.channel = channel
        self.method = method
        
        self.met_type = config.translate_options['type1']
        self.fit_variables = ''
        
        self.normalisation = {}
        self.initial_normalisation = {}
        self.templates = {}
        
    @mylog.trace()
    def save( self, output_path ):
        folder_template = '{path}/normalisation/{method}/{CoM}TeV/{variable}/{category}/'
        inputs = {
              'path': output_path,
              'CoM': self.config.centre_of_mass_energy,
              'variable': self.variable,
              'category': self.category,
              'method': self.method_string(),
              }
        output_folder = folder_template.format( **inputs )
        
        file_template = '{type}_{channel}_{met_type}.txt'
        inputs = {
                  'channel' : self.channel,
                  'met_type' : self.met_type,
                  }
        write_data_to_JSON(self.normalisation, 
                           output_folder + file_template.format(type = 'normalisation', **inputs))
        write_data_to_JSON(self.initial_normalisation, 
                           output_folder + file_template.format(type = 'initial_normalisation', **inputs))
        write_data_to_JSON(self.templates, 
                           output_folder + file_template.format(type = 'templates', **inputs))
        
        return output_folder
    
    @mylog.trace()    
    def method_string( self ):
        if self.method == self.BACKGROUND_SUBTRACTION:
            return 'background_subtraction'
        if self.method == self.SIMULTANEOUS_FIT:
            return 'simultaneous_fit_' + '_'.join( self.fit_variables )
        if self.method == self.FRACTION_FITTER:
            return 'fraction_fitter'
        
        return 'unknown_method'     

def parse_options():
    parser = OptionParser( __doc__ )
    parser.add_option( "-p", "--path", dest = "path", default = 'data',
                  help = "set output path for JSON files" )
    parser.add_option( "-v", "--variable", dest = "variable", default = 'MET',
                      help = "set the variable to analyse (MET, HT, ST, MT, WPT)" )
    parser.add_option( "-c", "--centre-of-mass-energy", dest = "CoM", default = 8, type = int,
                      help = "set the centre of mass energy for analysis. Default = 8 [TeV]" )
    parser.add_option( '-d', '--debug', dest = "debug", action = "store_true",
                      help = "Print the debug information" )
    parser.add_option( '--closure_test', dest = "closure_test", action = "store_true",
                      help = "Perform fit on data == sum(MC) * scale factor (MC process)" )
    parser.add_option( '--closure_test_type', dest = "closure_test_type", default = 'simple',
                      help = "Type of closure test (relative normalisation):" + '|'.join( closure_tests.keys() ) )
    parser.add_option( '--test', dest = "test", action = "store_true",
                      help = "Just run the central measurement" )
    
    ( options, args ) = parser.parse_args()
    return options, args

@mylog.trace()
def main():
    norm = TTJetNormalisation( 
                              config = measurement_config,
                              variable = variable,
                              category = 'central',
                              channel = 'electron',
                              method = TTJetNormalisation.BACKGROUND_SUBTRACTION,
                              )
    
    norm.save( output_path )
#     input_files_electron = get_input_files( 'central', 'electron' )
    
    

@mylog.trace() 
def get_input_files( category, channel ):
    # get data from histograms or JSON files
    # data and muon_QCD file with SFs are the same for central measurement and all systematics
    data_file, qcd_mc_file = None, None
    if channel == 'electron':
        data_file = File( measurement_config.data_file_electron )
        qcd_mc_file = File( measurement_config.electron_QCD_MC_file )
    if channel == 'muon':
        data_file = File( measurement_config.data_file_muon )
        qcd_mc_file = File( measurement_config.muon_QCD_MC_file )
    

    SingleTop_file = File( measurement_config.SingleTop_file )
    TTJet_file = File( measurement_config.ttbar_category_templates[category] )
    VJets_file = File( measurement_config.VJets_category_templates[category] )
    
    return {
                'TTJet': TTJet_file,
                'SingleTop': SingleTop_file,
                'V+Jets': VJets_file,
                'data': data_file,
                'QCD' : qcd_mc_file,
            }
    
@mylog.trace()
def get_histograms():
    electron_control_region = measurement_config.electron_control_region
    muon_control_region = measurement_config.muon_control_region

@mylog.trace()
def get_normalisation( method = 'background subtraction' ):
    '''
        Supported methods are 9or will be): 
            - background subtraction
            - Minuit (simultaneous fit)
            - TFractionFitter (fit to single variable)
    '''
    pass


if __name__ == '__main__':
    set_root_defaults()
    
    options, args = parse_options()

    # set global variables    
    debug = options.debug
    if debug:
        mylog.setLevel( log.DEBUG )
        
    measurement_config = XSectionConfig( options.CoM )
    # caching of variables for shorter access
    translate_options = measurement_config.translate_options
#     
#     ttbar_theory_systematic_prefix = measurement_config.ttbar_theory_systematic_prefix
#     vjets_theory_systematic_prefix = measurement_config.vjets_theory_systematic_prefix
#     generator_systematics = measurement_config.generator_systematics
#     categories_and_prefixes = measurement_config.categories_and_prefixes
#     met_systematics_suffixes = measurement_config.met_systematics_suffixes
#     analysis_type = measurement_config.analysis_types
#     run_just_central = options.closure_test or options.test
#     
    variable = options.variable
#     met_type = translate_options[options.metType]
#     b_tag_bin = translate_options[options.bjetbin]
#     b_tag_bin_VJets = translate_options[options.bjetbin_VJets]
#     path_to_files = measurement_config.path_to_files
    output_path = options.path
    if options.closure_test:
        output_path += '/closure_test/'
        output_path += options.closure_test_type + '/'
    
    main()
