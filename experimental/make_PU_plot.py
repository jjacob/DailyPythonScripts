#general
from optparse import OptionParser
import os, gc
from copy import deepcopy

# rootpy & matplotlib
from rootpy.io import File
from ROOT import kRed, kBlue, kGreen, kMagenta, kCyan, kBlack
from tools.ROOT_utililities import set_root_defaults

import matplotlib as matplotlib
from tools.plotting import get_best_max_y
matplotlib.use( 'agg' ) #Generate images without having a window appear
import rootpy.plotting.root2matplotlib as rootpyplot
import matplotlib.pyplot as pyplot
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MultipleLocator

from config import CMS
from matplotlib import rc
rc( 'font', **CMS.font )
rc( 'text', usetex = True )

if __name__ == '__main__':
    set_root_defaults()
    current_directory = os.getcwd() # return a string representing the current working directory.
    parser = OptionParser()
    parser.add_option( "-f", "--input_root_files", dest = "input_root_files", default = 'None',
                       help = "specify paths to input root files" )
    parser.add_option( "-o", "--output_folder", dest = "output_folder", default = current_directory,
                       help = "specify the path to save plots" )
    
    #set the formats to save the plots
    output_formats = ['pdf']
    
    #convert the script arguments to variables
    (options, args) = parser.parse_args()
    
    #set paths to input root files
    '7TeV_pu_down_file' = File( '' )
    '7TeV_pu_up_file' = File( '')
    '7TeV_pu_central_file' = 
    8TeV_pu
    
    histograms.
    
    
    pyplot.figure(figsize = CMS.figsize, dpi = CMS.dpi, facecolor = CMS.facecolor )
    axes = pyplot.axes()
    pyplot.xlabel( 'Number of interactions per crossing', CMS.x_axis_title )
    pyplot.ylabel( "Number of events", CMS.y_axis_title)
    plt.tick_params( **CMS.axis_label_major )
    plt.tick_params( **CMS.axis_label_minor )
    
    axes.minorticks_on()
    
    for key, hist in histograms.iteritems() :
        hist.linewidth = 2
        #set colours
        if "65835" in key or "central" in key:
            hist.SetLineColor( kRed )
        elif "69300" in key:
            hist.SetLineColor ( kBlue )
        elif "72765" in key:
            hist.SetLineColor ( kGreen )
    
    
    
    path = output_folder + 
    make_folder_if_not_exists( path )
    for output_format in output_formats:
        filename = path + "/pileup_distributions_fine_bin_for_AN" + output_format
        pyplot.savefig(filename)
    
    del hist
    pyplot.close()
    gc.collect()