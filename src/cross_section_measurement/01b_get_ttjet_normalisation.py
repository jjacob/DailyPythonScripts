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
from tools.ROOT_utils import set_root_defaults, get_histogram_from_file
from tools.logger import log
from config import XSectionConfig
from src.cross_section_measurement.lib import closure_tests
from tools.file_utilities import write_data_to_JSON
from tools.hist_utilities import clean_control_region, rebin_asymmetric,\
    hist_to_value_error_tuplelist
from config.variable_binning import bin_edges as variable_bin_edges

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

        self.have_normalisation = False

    @mylog.trace()
    def calculate_normalisation( self ):
        '''
            1. get file names
            2. get histograms from files
            3. scale histograms
            4. calculate normalisation based on self.method
        '''
        if self.have_normalisation:
            return
        input_files = self.get_input_files()

        histograms = self.get_histograms( input_files )
        histograms = self.scale_histograms( histograms )

        for sample, hist in histograms.items():
            # TODO: this should be a list of bin-contents
            self.initial_normalisation[sample] = hist_to_value_error_tuplelist(hist)
            if self.method == self.BACKGROUND_SUBTRACTION and sample != 'TTJet':
                self.normalisation[sample] = self.initial_normalisation[sample]

        if self.method == self.BACKGROUND_SUBTRACTION:
            ttjet_hist = clean_control_region(histograms,
                                              subtract = ['QCD', 'V+Jets', 'SingleTop'])
            self.normalisation['TTJet'] = hist_to_value_error_tuplelist(ttjet_hist)

        self.have_normalisation = True

    @mylog.trace()
    def get_input_files( self ):
        # get data from histograms or JSON files
        # data and muon_QCD file with SFs are the same for central measurement and all systematics
        data_file, qcd_mc_file = None, None
        if self.channel == 'electron':
            data_file = measurement_config.data_file_electron
            qcd_mc_file = measurement_config.electron_QCD_MC_file
        if self.channel == 'muon':
            data_file = measurement_config.data_file_muon
            qcd_mc_file = measurement_config.muon_QCD_MC_file

#         SingleTop_file = measurement_config.SingleTop_file
        SingleTop_file = measurement_config.SingleTop_category_templates[self.category]
        TTJet_file = measurement_config.ttbar_category_templates[self.category]
        VJets_file = measurement_config.VJets_category_templates[self.category]

        return {
                    'TTJet': TTJet_file,
                    'SingleTop': SingleTop_file,
                    'V+Jets': VJets_file,
                    'data': data_file,
                    'QCD' : qcd_mc_file,
                }

    @mylog.trace()
    def get_histograms( self, input_files ):
        if self.method == self.BACKGROUND_SUBTRACTION:
            histograms = self.get_histograms_for_background_subtraction( input_files )
            for sample, hist in histograms.items():
                bin_edges = variable_bin_edges[self.variable]
                histograms[sample] = rebin_asymmetric(hist, bin_edges)
            return histograms

    @mylog.trace()
    def get_histograms_for_background_subtraction( self, input_files ):
        # first, lets get the histograms from the signal region
        inputs = {
                    'channel' : measurement_config.analysis_types[self.channel],
                    'met_type' : self.met_type,
                    'selection' : 'Ref selection',
                    'btag' : measurement_config.translate_options['2m'],  # 2 or more
                  }
        variable_template = measurement_config.variable_path_templates[self.variable]
        hist = variable_template.format( **inputs )

        # QCD control region
        eqcd = measurement_config.electron_control_region
        muqcd = measurement_config.muon_control_region
        qcd_control_region = eqcd if self.channel == 'electron' else muqcd
        inputs['selection'] = qcd_control_region
        hist_qcd = variable_template.format( **inputs )

        histograms = {}
        control_region_hists = {}

        for sample, f in input_files.items():
            histograms[sample] = get_histogram_from_file( hist, f )
            # next get QCD control region
            if sample == 'QCD': # skip for QCD MC
                continue
            control_region_hists[sample] = get_histogram_from_file( hist_qcd, f )

        qcd_mc_hist = histograms['QCD']
        qcd_hist = clean_control_region( control_region_hists,
                                        subtract = ['TTJet', 'V+Jets', 'SingleTop'],
                                        )
        # normalise to MC prediction
        n_mc = qcd_mc_hist.Integral()
        n_data = qcd_hist.Integral()
        scale = 1
        if not n_data == 0:
            if not n_mc == 0:
                scale = 1 / n_data * n_mc
            else:
                scale = 1 / n_data
        qcd_hist.Scale(scale)
        histograms['QCD'] = qcd_hist

        return histograms

    @mylog.trace()
    def scale_histograms( self, histograms ):
        # scale rate-changing systematics
        variations = ['+', '-']
        print "histograms = ", histograms
        print "measurement_config.rate_changing_systematics = ", measurement_config.rate_changing_systematics
        for systematic, shift in measurement_config.rate_changing_systematics.iteritems():
            if options.test:
                continue

            for variation in variations:
                if variation == '+':
                    factor = 1.0 + shift
                elif variation == '-':
                    factor = 1.0 - shift

                self.category = systematic + variation
                print "self.category = ", self.category

                scale_factors = {}
                scale_factors[systematic + variation] = factor
                if systematic == 'TTJet_cross_section':
                    print "TTJet cross section"
                    histograms['TTJet'].Scale(factor)
                elif systematic == 'SingleTop_cross_section':
                    print "SingleTop cross section"
                    histograms['SingleTop'].Scale(factor)
                elif systematic == "luminosity":
                    print "luminosity"
                    for histogram in histograms:
                        print "histogram = ", histogram
                        if histogram == "data":
                            continue
                        histograms[histogram].Scale(factor)
                print "histograms = ", histograms
        #reset category to "central"
        self.category == "central"
        return histograms

    @mylog.trace()
    def save( self, output_path ):
        if not self.have_normalisation:
            self.calculate_normalisation()

        folder_template = '{path}/normalisation/{method}/{CoM}TeV/{variable}/{category}/'
        print "self.category = ", self.category
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
        write_data_to_JSON( self.normalisation,
                           output_folder + file_template.format( type = 'normalisation', **inputs ) )
        write_data_to_JSON( self.initial_normalisation,
                           output_folder + file_template.format( type = 'initial_normalisation', **inputs ) )
        write_data_to_JSON( self.templates,
                           output_folder + file_template.format( type = 'templates', **inputs ) )
        
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
    # for each measurement
    print "category = ", category
    norm = TTJetNormalisation( 
                              config = measurement_config,
                              variable = variable,
                              category = category, #'central',
                              channel = 'electron',
                              method = TTJetNormalisation.BACKGROUND_SUBTRACTION,
                              )
    
    norm.calculate_normalisation()
    norm.save( output_path )

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
    categories_and_prefixes = measurement_config.categories_and_prefixes
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

    print "categories_and_prefixes = ", categories_and_prefixes
    for category in categories_and_prefixes:
        category = category
        print "category = ", category
        main()
