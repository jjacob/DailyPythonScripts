'''
Created on 1 May 2014

@author: kreczko
'''
from collections import OrderedDict
from copy import copy, deepcopy

from optparse import OptionParser
from tools.ROOT_utils import get_histograms_from_files
from tools.hist_utilities import prepare_histograms, clean_control_region
from tools.file_utilities import make_folder_if_not_exists
from tools.plotting import make_data_mc_comparison_plot, Histogram_properties, make_shape_comparison_plot,\
    compare_measurements
from config.latex_labels import b_tag_bins_latex, samples_latex
from config.variable_binning import variable_bins_ROOT
from config import XSectionConfig
common_fit_variables = ['M3', 'M_bl', 'angle_bl']
electron_fit_variables = copy( common_fit_variables )
electron_fit_variables.append( 'electron_absolute_eta' )
muon_fit_variables = copy( common_fit_variables )
muon_fit_variables.append( 'muon_absolute_eta' )

fit_variable_properties = {
                       'M3': {'min':0, 'max':1000, 'rebin':5, 'x-title': 'M3 [GeV]', 'y-title': 'Events/25 GeV'},
                       'M_bl': {'min':0, 'max':400, 'rebin':2, 'x-title': 'M(b,l) [GeV]', 'y-title': 'Events/10 GeV'},
                       'angle_bl': {'min':0, 'max':3.5, 'rebin':2, 'x-title': 'angle(b,l)', 'y-title': 'Events/(0.2)'},
                       'electron_absolute_eta': {'min':0, 'max':2.6, 'rebin':2, 'x-title': '$\left|\eta(e)\\right|$', 'y-title': 'Events/(0.2)'},
                       'muon_absolute_eta': {'min':0, 'max':2.6, 'rebin':2, 'x-title': '$\left|\eta(\mu)\\right|$', 'y-title': 'Events/(0.2)'},
                       }

b_tag_bin = '2orMoreBtags'
b_tag_bin_ctl = '0orMoreBtag'
category = 'central'

variables = ['MET', 'HT', 'ST', 'WPT', 'MT']

save_as = ['pdf']
    
def main():
    global measurement_config, histogram_files
    global electron_fit_variables, muon_fit_variables, fit_variable_properties
    global b_tag_bin, category, histogram_files, variables
    global b_tag_bin_ctl
    
    title_template = 'CMS Preliminary, $\mathcal{L} = %.1f$ fb$^{-1}$  at $\sqrt{s}$ = %d TeV \n %s'
    e_title = title_template % ( measurement_config.new_luminosity / 1000., measurement_config.centre_of_mass_energy, 'e+jets, $\geq$ 4 jets' )
    met_type = 'patType1CorrectedPFMet'
    for variable in variables:
        variable_bins = variable_bins_ROOT[variable]
        histogram_template = get_histogram_template( variable )
        
        for fit_variable in electron_fit_variables:
            if '_bl' in fit_variable:
                b_tag_bin_ctl = '1orMoreBtag'
            else:
                b_tag_bin_ctl = '0orMoreBtag'
            save_path = 'plots/%dTeV/fit_variables/%s/%s/' % (measurement_config.centre_of_mass_energy, variable, fit_variable)
            make_folder_if_not_exists(save_path)
            make_folder_if_not_exists(save_path + 'qcd/')
            make_folder_if_not_exists(save_path + 'vjets/')
            for bin_range in variable_bins:
                params = {'met_type': met_type, 'bin_range':bin_range, 'fit_variable':fit_variable, 'b_tag_bin':b_tag_bin, 'variable':variable}
                fit_variable_distribution = histogram_template % params
                qcd_fit_variable_distribution = fit_variable_distribution.replace( 'Ref selection', 'QCDConversions' )
                qcd_fit_variable_distribution = qcd_fit_variable_distribution.replace( b_tag_bin, b_tag_bin_ctl )
                histograms = get_histograms_from_files( [fit_variable_distribution, qcd_fit_variable_distribution], histogram_files )
                plot_fit_variable( histograms, fit_variable, variable, bin_range, fit_variable_distribution, qcd_fit_variable_distribution, e_title, save_path )
        compare_qcd_control_regions(variable, met_type, e_title)
        compare_vjets_btag_regions(variable, met_type, e_title)
        
def get_histogram_template( variable ):     
    histogram_template = '' 
    if variable == 'HT':
        histogram_template = 'TTbar_plus_X_analysis/EPlusJets/Ref selection/Binned_HT_Analysis/HT_bin_%(bin_range)s/%(fit_variable)s_%(b_tag_bin)s'
    elif variable == 'MET':
        histogram_template = 'TTbar_plus_X_analysis/EPlusJets/Ref selection/Binned_MET_Analysis/%(met_type)s_bin_%(bin_range)s/%(fit_variable)s_%(b_tag_bin)s'
    else:
        histogram_template = 'TTbar_plus_X_analysis/EPlusJets/Ref selection/Binned_%(variable)s_Analysis/%(variable)s_with_%(met_type)s_bin_%(bin_range)s/%(fit_variable)s_%(b_tag_bin)s'
    return histogram_template
                      
def plot_fit_variable( histograms, fit_variable, variable, bin_range,
                      fit_variable_distribution, qcd_fit_variable_distribution,
                      title, save_path ):
    global fit_variable_properties, b_tag_bin, save_as, b_tag_bin_ctl
    mc_uncertainty = 0.10
    prepare_histograms( histograms, rebin = fit_variable_properties[fit_variable]['rebin'], scale_factor = measurement_config.luminosity_scale )
    
    histogram_properties = Histogram_properties()
    histogram_properties.x_axis_title = fit_variable_properties[fit_variable]['x-title']
    histogram_properties.y_axis_title = fit_variable_properties[fit_variable]['y-title']
    histogram_properties.x_limits = [fit_variable_properties[fit_variable]['min'], fit_variable_properties[fit_variable]['max']]

    histogram_lables = ['data', 'QCD', 'V+Jets', 'Single-Top', samples_latex['TTJet']]
    histogram_colors = ['black', 'yellow', 'green', 'magenta', 'red']
#     qcd_from_data = histograms['data'][qcd_fit_variable_distribution].Clone()
    # clean against other processes
    histograms_for_cleaning = {'data':histograms['data'][qcd_fit_variable_distribution],
                               'V+Jets':histograms['V+Jets'][qcd_fit_variable_distribution],
                               'SingleTop':histograms['SingleTop'][qcd_fit_variable_distribution],
                               'TTJet':histograms['TTJet'][qcd_fit_variable_distribution]}
    qcd_from_data = clean_control_region( histograms_for_cleaning, subtract = ['TTJet', 'V+Jets', 'SingleTop'] )
    
    
    histograms_to_draw = [histograms['data'][qcd_fit_variable_distribution],
                          histograms['QCD'][qcd_fit_variable_distribution],
                          histograms['V+Jets'][qcd_fit_variable_distribution],
                          histograms['SingleTop'][qcd_fit_variable_distribution],
                          histograms['TTJet'][qcd_fit_variable_distribution]]
    
    histogram_properties.title = title + ', ' + b_tag_bins_latex[b_tag_bin_ctl]
    histogram_properties.name = variable + '_' + bin_range + '_' + fit_variable + '_%s_QCDConversions' % b_tag_bin_ctl
    make_data_mc_comparison_plot( histograms_to_draw, histogram_lables, histogram_colors,
                                 histogram_properties,
                                 save_folder = save_path + '/qcd/',
                                 show_ratio = False,
                                 save_as = save_as,
                                 )
    
    histograms_to_draw = [qcd_from_data,
                          histograms['QCD'][qcd_fit_variable_distribution],
                          ]
    
    histogram_properties.name = variable + '_' + bin_range + '_' + fit_variable + '_%s_QCDConversions_subtracted' % b_tag_bin_ctl
    make_data_mc_comparison_plot( histograms_to_draw,
                                  histogram_lables = ['data', 'QCD'],
                                  histogram_colors = ['black', 'yellow'],
                                  histogram_properties = histogram_properties,
                                  save_folder = save_path + '/qcd/',
                                  show_ratio = False,
                                  save_as = save_as,
                                  )
    
    # scale QCD to predicted
    n_qcd_predicted_mc = histograms['QCD'][fit_variable_distribution].Integral()
    n_qcd_fit_variable_distribution = qcd_from_data.Integral()
    if not n_qcd_fit_variable_distribution == 0:
        qcd_from_data.Scale( 1.0 / n_qcd_fit_variable_distribution * n_qcd_predicted_mc )
    
    histograms_to_draw = [histograms['data'][fit_variable_distribution], qcd_from_data,
                          histograms['V+Jets'][fit_variable_distribution],
                          histograms['SingleTop'][fit_variable_distribution], histograms['TTJet'][fit_variable_distribution]]
    
    histogram_properties.title = title + ', ' + b_tag_bins_latex[b_tag_bin]
    histogram_properties.name = variable + '_' + bin_range + '_' + fit_variable + '_' + b_tag_bin
    make_data_mc_comparison_plot( histograms_to_draw,
                                  histogram_lables,
                                  histogram_colors,
                                  histogram_properties,
                                  save_folder = save_path,
                                  show_ratio = False,
                                  save_as = save_as,
                                 )
    histogram_properties.mc_error = mc_uncertainty
    histogram_properties.mc_errors_label = '$\mathrm{t}\\bar{\mathrm{t}}$ uncertainty'
    histogram_properties.name = variable + '_' + bin_range + '_' + fit_variable + '_' + b_tag_bin + '_templates'
    # change histogram order for better visibility
    histograms_to_draw = [histograms['TTJet'][fit_variable_distribution] + histograms['SingleTop'][fit_variable_distribution], 
                          histograms['TTJet'][fit_variable_distribution],
                          histograms['SingleTop'][fit_variable_distribution],
                          histograms['V+Jets'][fit_variable_distribution],
                          qcd_from_data]
    histogram_lables = ['QCD', 'V+Jets', 'Single-Top', samples_latex['TTJet'], samples_latex['TTJet'] + ' + ' + 'Single-Top']
    histogram_lables.reverse()
    # change QCD color to orange for better visibility
    histogram_colors = ['orange', 'green', 'magenta', 'red', 'black']
    histogram_colors.reverse()
    make_shape_comparison_plot( shapes = histograms_to_draw,
                                names = histogram_lables,
                                colours = histogram_colors,
                                histogram_properties = histogram_properties,
                                fill_area = False,
                                alpha = 1,
                                save_folder = save_path,
                                save_as = save_as,
                                )
    
    
def compare_qcd_control_regions( variable = 'MET', met_type = 'patType1CorrectedPFMet', title = 'Untitled'):
    ''' Compares the templates from the control regions in different bins
     of the current variable'''
    global fit_variable_properties, b_tag_bin, save_as, b_tag_bin_ctl
    variable_bins = variable_bins_ROOT[variable]
    histogram_template = get_histogram_template( variable )
    
    for fit_variable in electron_fit_variables:
        all_hists = {}
        inclusive_hist = None
        if '_bl' in fit_variable:
                b_tag_bin_ctl = '1orMoreBtag'
        else:
            b_tag_bin_ctl = '0orMoreBtag'
        save_path = 'plots/fit_variables/%dTeV/%s/%s/' % (measurement_config.centre_of_mass_energy, variable, fit_variable)
        make_folder_if_not_exists(save_path + '/qcd/')
        
        max_bins = 3
        for bin_range in variable_bins[0:max_bins]:
            
            params = {'met_type': met_type, 'bin_range':bin_range, 'fit_variable':fit_variable, 'b_tag_bin':b_tag_bin, 'variable':variable}
            fit_variable_distribution = histogram_template % params
            qcd_fit_variable_distribution = fit_variable_distribution.replace( 'Ref selection', 'QCDConversions' )
            qcd_fit_variable_distribution = qcd_fit_variable_distribution.replace( b_tag_bin, b_tag_bin_ctl )
            # format: histograms['data'][qcd_fit_variable_distribution]
            histograms = get_histograms_from_files( [qcd_fit_variable_distribution], histogram_files )
            prepare_histograms( histograms, rebin = fit_variable_properties[fit_variable]['rebin'], scale_factor = measurement_config.luminosity_scale )

            histograms_for_cleaning = {'data':histograms['data'][qcd_fit_variable_distribution],
                               'V+Jets':histograms['V+Jets'][qcd_fit_variable_distribution],
                               'SingleTop':histograms['SingleTop'][qcd_fit_variable_distribution],
                               'TTJet':histograms['TTJet'][qcd_fit_variable_distribution]}
            qcd_from_data = clean_control_region( histograms_for_cleaning, subtract = ['TTJet', 'V+Jets', 'SingleTop'] )
            # clean
            all_hists[bin_range] = qcd_from_data
    
        # create the inclusive distributions
        inclusive_hist = deepcopy(all_hists[variable_bins[0]])
        for bin_range in variable_bins[1:max_bins]:
            inclusive_hist += all_hists[bin_range]
        for bin_range in variable_bins[0:max_bins]:
            if not all_hists[bin_range].Integral() == 0:
                all_hists[bin_range].Scale(1/all_hists[bin_range].Integral())
        # normalise all histograms
        inclusive_hist.Scale(1/inclusive_hist.Integral())
        # now compare inclusive to all bins
        histogram_properties = Histogram_properties()
        histogram_properties.x_axis_title = fit_variable_properties[fit_variable]['x-title']
        histogram_properties.y_axis_title = fit_variable_properties[fit_variable]['y-title']
        histogram_properties.y_axis_title = histogram_properties.y_axis_title.replace('Events', 'a.u.')
        histogram_properties.x_limits = [fit_variable_properties[fit_variable]['min'], fit_variable_properties[fit_variable]['max']]
#         histogram_properties.y_limits = [0, 0.5]
        histogram_properties.title = title + ', ' + b_tag_bins_latex[b_tag_bin_ctl]
        histogram_properties.name = variable + '_' + fit_variable + '_' + b_tag_bin_ctl + '_QCD_template_comparison'
        measurements = {bin_range + ' GeV': histogram for bin_range, histogram in all_hists.iteritems()}
        measurements = OrderedDict(sorted(measurements.items()))
        compare_measurements(models = {'inclusive' : inclusive_hist}, 
                             measurements = measurements, 
                             show_measurement_errors = True, 
                             histogram_properties = histogram_properties, 
                             save_folder = save_path + '/qcd/', 
                             save_as = save_as)
        
def compare_vjets_btag_regions( variable = 'MET', met_type = 'patType1CorrectedPFMet', title = 'Untitled'):
    ''' Compares the V+Jets template in different b-tag bins'''
    global fit_variable_properties, b_tag_bin, save_as, b_tag_bin_ctl
    b_tag_bin_ctl = '0orMoreBtag'
    variable_bins = variable_bins_ROOT[variable]
    histogram_template = get_histogram_template( variable )
    
    for fit_variable in electron_fit_variables:
        if '_bl' in fit_variable:
                b_tag_bin_ctl = '1orMoreBtag'
        else:
            b_tag_bin_ctl = '0orMoreBtag'
        save_path = 'plots/fit_variables/%dTeV/%s/%s/' % (measurement_config.centre_of_mass_energy, variable, fit_variable)
        make_folder_if_not_exists(save_path + '/vjets/')
        histogram_properties = Histogram_properties()
        histogram_properties.x_axis_title = fit_variable_properties[fit_variable]['x-title']
        histogram_properties.y_axis_title = fit_variable_properties[fit_variable]['y-title']
        histogram_properties.y_axis_title = histogram_properties.y_axis_title.replace('Events', 'a.u.')
        histogram_properties.x_limits = [fit_variable_properties[fit_variable]['min'], fit_variable_properties[fit_variable]['max']]
        histogram_properties.title = title + ', ' + b_tag_bins_latex[b_tag_bin_ctl]
        for bin_range in variable_bins:
            params = {'met_type': met_type, 'bin_range':bin_range, 'fit_variable':fit_variable, 'b_tag_bin':b_tag_bin, 'variable':variable}
            fit_variable_distribution = histogram_template % params
            fit_variable_distribution_ctl = fit_variable_distribution.replace( b_tag_bin, b_tag_bin_ctl )
            # format: histograms['data'][qcd_fit_variable_distribution]
            histograms = get_histograms_from_files( [fit_variable_distribution, fit_variable_distribution_ctl], {'V+Jets' : histogram_files['V+Jets']} )
            prepare_histograms( histograms, rebin = fit_variable_properties[fit_variable]['rebin'], scale_factor = measurement_config.luminosity_scale )
            histogram_properties.name = variable + '_' + bin_range + '_' + fit_variable + '_' + b_tag_bin_ctl + '_VJets_template_comparison'
            histograms['V+Jets'][fit_variable_distribution].Scale(1/histograms['V+Jets'][fit_variable_distribution].Integral())
            histograms['V+Jets'][fit_variable_distribution_ctl].Scale(1/histograms['V+Jets'][fit_variable_distribution_ctl].Integral())
            compare_measurements(models = {'no b-tag' : histograms['V+Jets'][fit_variable_distribution_ctl]}, 
                             measurements = {'$>=$ 2 b-tags': histograms['V+Jets'][fit_variable_distribution]}, 
                             show_measurement_errors = True, 
                             histogram_properties = histogram_properties, 
                             save_folder = save_path + '/vjets/', 
                             save_as = save_as)
            
if __name__ == '__main__':
  parser = OptionParser()
  parser.add_option( "-c", "--centre-of-mass-energy", dest = "CoM", default = 8, type = int,
                    help = "set the centre of mass energy for analysis. Default = 8 [TeV]" )
  ( options, args ) = parser.parse_args()
  
  measurement_config = XSectionConfig( options.CoM )

  histogram_files = {
        'data' : measurement_config.data_file_electron,
        'TTJet': measurement_config.ttbar_category_templates[category],
        'V+Jets': measurement_config.VJets_category_templates[category],
        'QCD': measurement_config.electron_QCD_MC_file,  # this should also be category-dependent, but unimportant and not available atm
        'SingleTop': measurement_config.SingleTop_category_templates[category]
  }

  main()
