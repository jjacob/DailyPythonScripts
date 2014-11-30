import os as os
import sys as sys
import re as re
import ROOT as ROOT
from optparse import OptionParser
import commands as commands
import fnmatch as fnmatch
import glob as glob

username=os.getlogin()
username="jjacob"
path_to_DailyPythonScripts= "/storage/" + username + "/03_Measurement/CMSSW_6_0_1_DailyPythonScripts/src/DailyPythonScripts/"
job_directories=[#"TT_noCorr_7TeV-mcatnlo_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TT_TuneZ2_7TeV-mcatnlo_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TT_TuneZ2_7TeV-powheg-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TT_TuneZ2_7TeV-pythia6-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TTJets_TuneP11noCR_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
				"TTjets_TuneZ2_matchingdown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v3_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TTjets_TuneZ2_matchingup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TTjets_TuneZ2_scaledown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v3_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"TTjets_TuneZ2_scaleup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v3_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"WJetsToLNu_TuneZ2_matchingdown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"WJetsToLNu_TuneZ2_matchingup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"WJetsToLNu_TuneZ2_scaledown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"WJetsToLNu_TuneZ2_scaleup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"ZJetsToLL_TuneZ2_matchingdown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"ZJetsToLL_TuneZ2_matchingup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"ZJetsToLL_TuneZ2_scaledown_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013",
#				"ZJetsToLL_TuneZ2_scaleup_7TeV-madgraph-tauola_Fall11-PU_S6_START44_V9B-v1_nTuple_v10_LeptonPlus3Jets_Dec2013"
				]

def crab_status(job_directory):
	ROOT.gROOT.SetBatch(True)

#	parser = OptionParser("Script to check progress of CRAB jobs in creating nTuples. Run as: python check_CRAB_jobs.py {-p projectFolder(e.g./gpfs_phys/storm/cms/user/...) -n numberOfJobs} >&check.log &")
	parser = OptionParser("Script to check progress of CRAB jobs in creating nTuples. Run as: python check_CRAB_jobs.py followed by desired options.")
	parser.add_option("-f", "--forceResubmit", action="store_true", dest="forceResubmit", default=False,
					help="opt to verify which files are not on the Bristol T2 Storage Element and forceResubmit any which are not present or are corrupted. WARNING: using this option will take a long time, about 1 hour for a submission with 2000 jobs.")
#	parser.add_option("-p", "--projectFolder", dest="projectFolder",
#					help="specify project folder.")
#	parser.add_option("-n", "--numberOfJobs", dest="numberOfJobs",
#					help="specify number of jobs in CRAB submission.")
#	parser.set_defaults(forceResubmit=False)
	(options, args) = parser.parse_args()
	
   	projectFolder = "/gpfs_phys/storm/cms/user/" + username + "/" + job_directory + "/"
    
	#make sure the project option has been specified
#	if not options.projectFolder:
#		parser.error('Please enter a project folder as the -p option: /gpfs_phys/storm/cms/user/...')

	#normalise the projectFolder filepath and add a "/" at the end
	projectFolder = os.path.normpath(projectFolder) + os.sep
	print projectFolder
	print options.forceResubmit
	print options

	#The following section has been commented out because if it is the first time this script is being run in a session, a grid password will be needed which will cause the script
	#to not be able to finish. Since the only purpose of this following CRAB command is to obtain the number of jobs, for the time being the number of jobs has been entered as an option to
	#the script which should be manually entered by the user.

	#get the status of the crab jobs and extract the number of output files expected on the Bristol Storage Element.
	projectFolder = projectFolder.split("/")[6]
	#don't redirect output from the first one because you will need to enter your grid password
	if job_directories.index(job_directory) == 0:
		status_output = commands.getstatusoutput("crab -status -c " + job_directory)
	else:
		status_output = commands.getstatusoutput("crab -status -c " + job_directory + " >&check_" + job_directory + ".log")
	numberOfJobs = get_number_jobs(status_output)

	#Now, check that all job root files are present in Bristol Storage Element folder:
	missingOrBrokenTemp = []
	missingOrBroken = []
	goodFilesTemp = []
	goodFiles = []
	presentJobList = []
	duplicatesToDelete = []

	#make list of all the job numbers which should be present.
	jobList = range(1,int(numberOfJobs)+1)

	#Open logfile (in append mode) to write to
	logfile = open("check_" + job_directory + ".log", 'a')

	if options.forceResubmit == True:
		logfile.write("Force Resubmitting.\n")
		
		#list the items in the CRAB output folder on the Bristol Storage Element.
		storageElementList=glob.glob(projectFolder + "*.root")
		if storageElementList:
			pass
		else:
			print "Location Error: Specified project folder does not exist on the Bristol Storage Element, signifying that the CRAB job has probably not started running yet or you forgot to include the full path /gpfs_storm/cms/user/..."
			sys.exit()
		
		#try opening all files in Bristol Storage Element folder and add to missing list if they cannot be opened.
		for file in storageElementList:
			#make list of all jobs numbers in the Bristol Storage Element folder
			jobNumber = int((re.split('[\W+,_]',file))[-4])
			presentJobList.append(jobNumber)
	
			#check if files are corrupt or not
			try:
				rootFile = ROOT.TFile.Open(file)
				rootFile.Close()
			except:
				logfile.write("Adding Job Number", jobNumber, "to missingOrBroken list because file is corrupted.")
				missingOrBrokenTemp.append(jobNumber)
			else:
				goodFilesTemp.append(jobNumber)
		
		#now add any absent files to the missing list:
		for job in jobList:
			if job not in presentJobList:
				logfile.write("Adding Job Number", job, "to missingOrBroken list because it doesn't exist on the Storage Element.")
				missingOrBrokenTemp.append(job)
		
		#Remove any job numbers from missingOrBroken which appear in both goodFiles and missingOrBroken lists
		for job in missingOrBrokenTemp:
			if job not in goodFilesTemp:
				missingOrBroken.append(job)
			else:
				logfile.write("Removing", job, "from missingOrBroken list because there is at least one duplicate good output file.")
		
		#Remove any job numbers from goodFiles which appear more than once in goodFiles
		for job in goodFilesTemp:
			if job not in goodFiles:
				goodFiles.append(job)
			else:
				duplicatesToDelete.append(job)
		
		#Write to logfile
		logfile.write("\n The following", len(goodFiles), "good output files were found in the Bristol Storage Element folder:")
		logfile.write(str(goodFiles).replace(" ", ""))
		logfile.write("\n The following", len(duplicatesToDelete), "job numbers have multiple good files on the Bristol Storage Element folder which can be deleted:")
		logfile.write(str(duplicatesToDelete).replace(" ", ""))
		logfile.write("\n The following", len(missingOrBroken), "job numbers could not be found in the Bristol Storage Element folder:")
		logfile.write(str(missingOrBroken).replace(" ", ""))
		logfile.write("\n")
		logfile.close()

		#forceResubmit the missing or broken files on the the Bristol Storage Element
		commands.getstatusoutput("crab -forceResubmit " + missingOrBroken + " -c " + job_directory + " >>check_" + job_directory + ".log 2>&1")

	else:
		logfile.write("Only resubmitting.\n")
		logfile.close()
		
		#Get crab outputs and resubmit bad jobs
		commands.getstatusoutput("crab -get -c " + job_directory + " >>check_" + job_directory + ".log 2>&1")
		commands.getstatusoutput("crab -resubmit bad -c " + job_directory + " >>check_" + job_directory + ".log 2>&1")
		
def get_number_jobs(status_output):
	#Split the crab -status output and find the total number of jobs
	statusFormatted = status_output[1].split("\n")
	for line in statusFormatted:
		if "crab:" in line and "Total Jobs" in line:
			words = line.split()
			numberOfJobs = int(words[1])
			return numberOfJobs
#def get_unfinished_jobs(status_output):
#	#Split the crab -status output and find the total number of jobs
#	statusFormatted = status_output[1].split("\n")
#	for line in statusFormatted:
#		if ""
	
if __name__ == '__main__':
	for job_directory in job_directories:
		crab_status(job_directory)