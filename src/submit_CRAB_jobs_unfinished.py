import os
import sys
from optparse import OptionParser
import commands


parser = OptionParser("Script to check progress of CRAB jobs in creating nTuples. Run as: python check_CRAB_jobs.py followed by desired options.")
parser.add_option("-f", "--forceResubmit", action="store_true", dest="forceResubmit", default=False, 
                      help="opt to verify which files are not on the Bristol T2 Storage Element and forceResubmit any which are not present or are corrupted. WARNING: using this option will take a long time, about 1 hour for a submission with 2000 jobs.")
parser.add_option("-p", "--path_to_configuration_files", action="store_true", dest="path_to_configuration_files", default="",
                      help="specify path to configuration files e.g. /storage/<username>/CMSSW_X_X_X/src/BristolAnalysis/NTupleTools/Configuration/... default = "" ")




configuration_files_folder = options.path_to_configuration_files + "/"

configuration_files = []


print "Creating and submitting jobs from the following configuration files:\n"
for file in os.listdir(configuration_files_folder):
        print file, "\n"
        configuration_files.add(file)
        status_output = commands.getstatusoutput("crab -create -cfg " + configuration_files_folder + file)
        
        status_output = commands.getstatusoutput("crab -submit -c 

