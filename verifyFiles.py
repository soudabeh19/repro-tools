#!/usr/bin/env python

# #verifyFiles.py
#
# Script to check whether the output files generated across 
# subject folders in different conditions are the same or not.
#

import os
import sys
import subprocess
import commands
import argparse,textwrap
import hashlib
import operator
import logging
import csv
import sqlite3
import re

# Returns a dictionary where the keys are the paths in 'directory'
# (relative to 'directory') and the values are the os.stat objects
# associated with these paths. By convention, keys representing
# directories have a trailing '/'.
def get_dir_dict(directory,exclude_items): 
    result_dict={}
    for root,dirs,files in os.walk(directory):
	if exclude_items is not None:
	    dirs[:]=[d for d in dirs if d not in exclude_items]
            files[:]=[f for f in files if f not in exclude_items] 
        for file_name in files:
            abs_file_path=os.path.join(root,file_name)
	    rel_path=abs_file_path.replace(os.path.join(directory+"/"),"")
            result_dict[rel_path]=os.stat(abs_file_path)
    return result_dict

# Returns a dictionary where the keys are the directories in
# 'condition_dir' and the values are the directory dictionaries (as
# returned by get_dir_dict) associated to these directories.
def get_condition_dict(condition_dir,exclude_items):
    condition_dict={}
    subject_names_list=[]
    subject_names_list[:]=[subject_name for subject_name in os.listdir(condition_dir)]
    if exclude_items is not None:
        subject_names_list[:]=[subject_name for subject_name in subject_names_list if subject_name not in exclude_items]
    for subject_name in subject_names_list:
        subject_dir_path=os.path.join(condition_dir,subject_name)
        if os.path.isdir(subject_dir_path):
            condition_dict[subject_name]=get_dir_dict(subject_dir_path,exclude_items)
    return condition_dict

# Returns a dictionary where the keys are the names in
# 'condition_names' and the values are the corresponding condition
# dictionaries (as returned by get_condition_dict)
def get_conditions_dict(condition_names,root_dir,exclude_items):
    conditions_dict={}
    if exclude_items is not None:
        condition_names[:]=[condition for condition in condition_names if condition not in exclude_items]
    for condition in condition_names:
        conditions_dict[condition]=get_condition_dict(os.path.join(root_dir,condition),exclude_items)
    return conditions_dict

# Returns a list where each element is a line in 'file_name'
def read_file_contents(file_name):
    with open(file_name, 'r') as infile:
        data=infile.read()  
        directory_list=data.splitlines()
    return directory_list

# Parses the metrics from the metrics file
def read_metrics_file(file_name):
    metrics = {}
    if file_name is None:
        return metrics
    with open(file_name, 'r') as csvfile:
        linereader = csv.reader(csvfile,delimiter=',')
        for row in linereader:
            metric = {}
            metric['name']=row[0]
            metric['extension']=row[1]
            metric['command']=row[2]
            metric['output_file']=row[3]
            metrics[metric['name']]=metric
    return metrics

# Returns the checksum of path 'path_name'
def checksum(path_name):
    hasher=hashlib.md5()
    if os.path.isfile(path_name):
        md5_sum=file_hash(hasher,path_name)
    elif os.path.isdir(path_name):
        md5_sum=directory_hash(hasher,path_name)
    return md5_sum

# Method file_hash is used for generating md5 checksum of a file 
# Input parameters: file name and hasher
def file_hash(hasher,file_name):
    file_content=open(file_name)
    while True:
        read_buffer=file_content.read(2**20)
        if len(read_buffer)==0: 
            break
        hasher.update(read_buffer)
    file_content.close()
    return hasher.hexdigest()

# Method directory_hash collects the directory and file names from the directory given as input.
# Checksum is created on the basis of filenames and directories present in the file input directory.
# #Input parameters: hashed content , path 
def directory_hash(hasher, dir_path):
    if os.path.isdir(dir_path):
        for entry in sorted(os.listdir(dir_path)):
            hasher.update(entry)
    return hasher.hexdigest()

# Stops the execution if not all the subjects of all the conditions
# have the same list of files
def check_files(conditions_dict):
    path_names=set()
    for condition in conditions_dict:
        for subject in conditions_dict[condition]:
            path_names.update(conditions_dict[condition][subject].keys())
    for path_name in path_names:
        for condition in conditions_dict.keys():
            for subject in conditions_dict[condition].keys():
                if not path_name in conditions_dict[condition][subject].keys():
                    log_error("File \"" + path_name  + "\" is missing in subject \"" + subject + "\" of condition \"" + condition + "\".")

# Returns a dictionary where the keys identifies two conditions
# (e.g. "condition1 vs condition2") and the values are dictionaries
# where the keys are path names common to these two conditions and the
# values are the number of times that this path differs among all
# subjects of the two conditions.
# For instance:
#  {'condition1 vs condition2': {'c/c.txt': 0, 'a.txt': 2}}
#  means that 'c/c.txt' is identical for all subjects in conditions condition1 and condition2 while 'a.txt' differs in two subjects.
def n_differences_across_subjects(conditions_dict,root_dir,metrics,checksums_from_file_dict,checksum_after_file_path,check_corruption,sqlite_db_path):
    # For each pair of conditions C1 and C1
    product = ((i,j) for i in conditions_dict.keys() for j in conditions_dict.keys())
    diff={} # Will be the return value
    metric_values={}
    path_names = conditions_dict.values()[0].values()[0].keys()
    #dictionary_checksum is used for storing the computed checksum values and to avoid computing the checksums for the files multiple times
    dictionary_checksum={}
    #dictionary_executables is used for tracking the files that we have already found the executables for
    dictionary_executables={}
    #Initialize sqlite connection
    if sqlite_db_path:
      try:
        conn = sqlite3.connect(sqlite_db_path)
      except sqlite3.Error, e:
        log_error(e)
    # Go through all pairs of conditions
    for c, d in product:
        if c < d: # Makes sure that pairs are not ordered, i.e. {a,b} and {b,a} are the same
            key=c+" vs "+d
            diff[key]={}
            # if c and d both start with x-RUN-y (same x, different
            # y), then assume that they are different runs from the
            # same condition. In this case, if there are differences
            # for a given file name below, the reprozip trace should
            # be inspected to determine the executable that created
            # such inter-run differences in the same condition. Also,
            # print a log_info saying "Identified c1 and c2 as two
            # different runs of the same condition".
	    is_intra_condition_run=False
	    pattern = re.compile('.*-RUN-[0-9]*')
	    if pattern.match(c) and pattern.match(d):
	      condition_c=c.split("-")
	      condition_d=d.split("-")
	    
	    #Checking if the runs are intra runs on the same condition(Operating System).
	      if (condition_c and condition_d) and (condition_c[0]==condition_d[0]):
		log_info("Identified " + c +" and " + d +" as two different runs of the same condition")
		is_intra_condition_run=True
	        
   
            for file_name in path_names:
                diff[key][file_name]=0
                for subject in conditions_dict[c].keys():
                # Here we assume that both conditions will have the same set of subjects
                    files_are_different=False
		    abs_path_c=os.path.join(root_dir,c,subject,file_name)
                    abs_path_d=os.path.join(root_dir,d,subject,file_name)
		    if checksums_from_file_dict:
		      if (checksums_from_file_dict[c][subject][file_name] != checksums_from_file_dict[d][subject][file_name]):
                        diff[key][file_name]+=1
                        files_are_different=True
		    elif conditions_dict[c][subject][file_name].st_size != conditions_dict[d][subject][file_name].st_size :
		      diff[key][file_name]+=1
                      files_are_different=True
		    elif abs_path_c in dictionary_checksum and  abs_path_d in dictionary_checksum:
		      if is_checksum_equal(dictionary_checksum,abs_path_c,abs_path_d):
		        diff[key][file_name]+=1
			files_are_different=True
		    elif abs_path_c not in dictionary_checksum and abs_path_d in dictionary_checksum:
		      dictionary_checksum[abs_path_c]=checksum(abs_path_c)
		      if is_checksum_equal(dictionary_checksum,abs_path_c,abs_path_d):
			diff[key][file_name]+=1
			files_are_different=True
		    elif abs_path_c in dictionary_checksum and abs_path_d not in dictionary_checksum:
		      dictionary_checksum[abs_path_d] = checksum(abs_path_d)
		      if is_checksum_equal(dictionary_checksum,abs_path_c,abs_path_d):
			diff[key][file_name]+=1
			files_are_different=True
		    else:
		      dictionary_checksum[abs_path_d] = checksum(abs_path_d)
		      dictionary_checksum[abs_path_c] = checksum(abs_path_c)
                      if is_checksum_equal(dictionary_checksum,abs_path_c,abs_path_d):
                        diff[key][file_name]+=1
                        files_are_different=True

                    if files_are_different:
			#Below condition is making sure that the checksums are getting read from the file.Also that we are not computing the checksum of the checksums-after file.
			if check_corruption and checksums_from_file_dict and checksum_after_file_path not in file_name:
			     #If the checksum of the file computed locally is different from the one in the file, the file got corrupted and hence throw error. 
			     if (checksum(abs_path_c) != checksums_from_file_dict[c][subject][file_name]):
                               log_error("Checksum of\"" + abs_path_c + "\"in checksum file is different from what is computed here.")
			     #If the checksum of the file computed locally is different from the one in the file, the file got corrupted and hence throw error.
                             if (checksum(abs_path_d) != checksums_from_file_dict[d][subject][file_name]):
                               log_error("Checksum of\"" + abs_path_d + "\"in checksum file is different from what is computed here.")
                        metrics_to_evaluate = get_metrics(metrics,file_name)
                        if len(metrics_to_evaluate) != 0:
                            for metric in metrics.values():
                                if metric['name'] not in metric_values.keys():
                                    metric_values[metric['name']]={}
                                if key not in metric_values[metric['name']].keys():
                                    metric_values[metric['name']][key] = {}
                                if file_name not in metric_values[metric['name']][key].keys():
                                    metric_values[metric['name']][key][file_name]=0
                                metric_values[metric['name']][key][file_name] += float(run_command(metric['command'],file_name,c,d,subject,root_dir))
                        # if we are in different runs of the same
                        # condition (see previous comment) then
                        # inspect the reprozip trace here to get the
                        # list of executables that created such
                        # differences
		        if sqlite_db_path and files_are_different and file_name not in dictionary_executables:
			  #Monitor.txt seems not to have entry in sqlite table
			   if is_intra_condition_run:
			     #** indicates that the entries are the result of an intra-condition run
			     dictionary_executables["**"+file_name]=get_executable_details(conn,sqlite_db_path,file_name)
			   else:
			     dictionary_executables[file_name]=get_executable_details(conn,sqlite_db_path,file_name)
    if sqlite_db_path:
      conn.close()
    return diff,metric_values,dictionary_executables

#Method is_checksum_equal will return True if the checksums are not equal
def is_checksum_equal(dictionary_checksum,abs_path_c,abs_path_d):
    return dictionary_checksum[abs_path_c] != dictionary_checksum[abs_path_d]

#Method get_executable_details is used for finding out the details of the processes that created or modified the specified file.
def get_executable_details(conn,sqlite_db_path,file_name):#TODO Intra condition run is not taken into account while the executable details are getting written to the file
    sqlite_cursor = conn.cursor()
    #opened_files table has a column named MODE
    # The definition of the mode values are as described below
    #FILE_READ =1
    #FILE_WRITE=2
    #FILE_WDIR=4
    #FILE_STAT=8
    #FILE_LINK=16
    sqlite_cursor.execute('SELECT DISTINCT executed_files.name,executed_files.argv,executed_files.envp,executed_files.timestamp,executed_files.workingdir from executed_files INNER JOIN opened_files where opened_files.process = executed_files.process and opened_files.name like ? and opened_files.mode=2 and opened_files.is_directory=0',('%/'+file_name,))
    data = sqlite_cursor.fetchall()
    sqlite_cursor.close()    
    executable_details_list=[]
    if data:
      for row in data:
	#Adding to a list, all the processes and the details which operated on the given file
	executable_details_list.append(row)
    return executable_details_list

# Returns the list of metrics associated with a given file name, if any
def get_metrics(metrics,file_name):
    matching_metrics = []
    for metric in metrics.values():
        if file_name.endswith(metric['extension']):
            matching_metrics.append(metric)
    return matching_metrics

# Executes the following command:
#    'command condition1/subject_name/file_name condition2/subject_name/file_name'
# and returns the stdout if and only if command was successful
def run_command(command,file_name,condition1,condition2,subject_name,root_dir):
    command_string = command+" "+os.path.join(root_dir,condition1,subject_name,file_name)+" "+os.path.join(root_dir,condition2,subject_name,file_name)
    return_value,output = commands.getstatusoutput(command_string)
    if return_value != 0:
        log_error("Command "+ command +" failed.")
    return output

#Method read_checksum_from_file gets the file path containing the checksum and the file name.
#It reads the content line by line and if a match is found, it adds the file name as key and checksum as the value and returns dictionary after 
#the file gets read.
def read_checksum_from_file(checksums_after_file_path):
    checksum_from_file_dict={}
    with open(checksums_after_file_path) as file:
         for line in file:
	     if (len(line.split(' ', 1)) == 2) and '/' in line:
		 filename=((line.split(' ', 1)[1]).strip())
		 filename=filename.split('/', 2)[2]
	         checksum_from_file_dict[filename]=(line.split(' ', 1)[0]).strip()
    return checksum_from_file_dict

#Method get_conditions_checksum_dict creates a dictionary containing , the dictionaries under different condition with the condition as the key and subject
#folder dictionaries as the value.
def get_conditions_checksum_dict(conditions_dict,root_dir,checksum_after_file_path):
    conditions_checksum_dict={}
    conditions=conditions_dict.keys()
    subjects=conditions_dict.values()[0].keys()
    for condition in conditions:
	conditions_checksum_dict[condition]=get_condition_checksum_dict(condition,root_dir,subjects,checksum_after_file_path)
    return conditions_checksum_dict

#Method get condition checksum dictionary, creates a dictionary with subject as key,
#and associated files and checksums as values.
def get_condition_checksum_dict(condition,root_dir,subjects,checksum_after_file_path):
    condition_checksum_dict={}
    for subject in subjects:
        condition_checksum_dict[subject]=read_checksum_from_file(os.path.join(root_dir,condition,subject,checksum_after_file_path))
    return condition_checksum_dict

# Returns a string containing a 'pretty' matrix representation of the
# dictionary returned by n_differences_across_subjects
def pretty_string(diff_dict,conditions_dict):
    output_string=""
    max_comparison_key_length=0
    max_path_name_length=0
    first=True
    path_list=[]
    first_condition=conditions_dict[conditions_dict.keys()[0]]
    first_subject=first_condition[first_condition.keys()[0]]
    for comparison in diff_dict.keys():
        l = len(comparison)
        if l > max_comparison_key_length:
            max_comparison_key_length=l
        if first:
            for path in diff_dict[comparison].keys():
                path_list.append({'name': path, 'mtime': first_subject[path].st_mtime})
                if len(path) > max_path_name_length:
                    max_path_name_length = len(path)
            first=False
    # First line
    for i in range(1,max_path_name_length):
        output_string+=" "
    output_string+="\t"
    for comparison in diff_dict.keys():
        output_string+=comparison+"\t"
    output_string+="\n"
    # Next lines
    path_list.sort(key=lambda x: x['mtime']) # the sort key (name or mtime) could be a parameter
    for path_dict in path_list:
        path=path_dict['name']
        output_string+=path
        for i in range(1,max_path_name_length-len(path)):
            output_string+=" "
        output_string+="\t"
        for comparison in diff_dict.keys():
            for i in range(1,max_comparison_key_length/2):
                output_string+=" "
            value=str(diff_dict[comparison][path])
            output_string+=value
            for i in range(1,max_comparison_key_length/2+1):
                output_string+=" "
            output_string+="\t"
        output_string+="\n"
    return output_string

# Method check_subjects checks if the subject_folders under different conditions are the same. If not , it stops the execution of the script.
def check_subjects(conditions_dict):
    subject_names=set()
    for condition in conditions_dict.keys():
	subject_names.update(conditions_dict[condition].keys())
   # Iterate over each soubject in every condition and stop the execution if some subject is missing
    for subject in subject_names:
       for condition in conditions_dict.keys():
          if not subject in conditions_dict[condition].keys():
	     log_error("Subject \"" + subject + "\" is missing under condition \""+ condition +"\"." )

# Logging functions

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error("ERROR: " + message)
    sys.exit(1)

def main():
        parser=argparse.ArgumentParser(description="verifyFiles.py" ,formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("file_in", help= textwrap.dedent('''Input the text file containing the path to the condition folders
                                             Each directory contains subject folders containing subject-specific and modality-specific data categorirzed into different
					     subdirectories.
					     Sample:
					     Format : <subject_id>/unprocessed/3T/
					     Unprocessed data for exemplar subject 100307 unpacks to the following directory structure:
					     100307/unprocessed/3T/
					     100307_3T.csv
    					     Diffusion
    					     rfMRI_REST1_LR
    					     rfMRI_REST1_RL
    					     rfMRI_REST2_LR
    					     rfMRI_REST2_RL
    					     T1w_MPR1
    					     T2w_SPC1
					     ....
					     ...
					     These subdirectories will be processed under  different conditions.
					     Conditions refer to the operating system  on which the process is ran or the version of the pipeline which is used to process the data.
                                             An example would be a directory containing the files processed using CentOS6 operating system and PreFreeSurfer version 5.0.6
                                             Sample of the input file
                                             /home/$(USER)/CentOS6.FSL5.0.6
                                             /home/$(USER)/CentOS7.FSL5.0.6
                                             Each directory will contain subject folders like 100307,100308 etc'''))
        parser.add_argument("-c", "--checksumFile",help="Reads checksum from files. Doesn't compute checksums locally")
	parser.add_argument("-d", "--fileDiff", help="Writes the difference matrix into a file")
        parser.add_argument("-m", "--metricsFile", help="CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name") 
        parser.add_argument("-e","--excludeItems",help="The list of items to be ignored while parsing the files and directories")
	parser.add_argument("-k","--checkCorruption",help="If this flag is kept 'TRUE', it checks whether the file is corrupted")
	parser.add_argument("-s","--sqLiteFile",help="The path to the sqlite file which is used as the reference file for identifying the processes which created the files")
	parser.add_argument("-x","--execFile",help="Writes the executable details to a file")
	args=parser.parse_args()
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
	if not os.path.isfile(args.file_in):
	  log_error("The input file path of conditions file is not correct")
        conditions_list=read_file_contents(args.file_in)
        root_dir=os.path.dirname(os.path.abspath(args.file_in))
        log_info("Walking through files...")
	checksums_from_file_dict={}
	#exclude_items is a list containing the folders and files which should be ignored while traversing 
	#through the directories
	exclude_items=None
	if args.excludeItems:
	  if not os.path.isfile(args.excludeItems):
	    log_error("The input file path of exclude items file is not correct")
        exclude_items=read_file_contents(args.excludeItems)
        conditions_dict=get_conditions_dict(conditions_list,root_dir,exclude_items)
        log_info("Checking if subject folders are missing in any condition...")
	check_subjects(conditions_dict)
	log_info("Checking if files are missing in any subject of any condition...")
	check_files(conditions_dict)
        log_info("Reading the metrics file...")
        metrics = read_metrics_file(args.metricsFile)
        log_info("Computing differences across subjects...")
	if args.checksumFile:
            log_info("Reading checksums from files...")
            checksums_from_file_dict=get_conditions_checksum_dict(conditions_dict,root_dir,args.checksumFile)
	#Checking whether sqlite file path alone or executable file name alone is given. In case only one is given, throw error.
	if (args.sqLiteFile and args.execFile is None) or (args.execFile and args.sqLiteFile is None):
          log_error("Input the SQLite file path and the name of the file to which the executable details should be saved")
	#Differences across subjects needs the conditions dictionary, root directory, checksums_from_file_dictionary,
	#and the file checksumFile,checkCorruption and the path to the sqlite file.
        diff,metric_values,dictionary_executables=n_differences_across_subjects(conditions_dict,root_dir,metrics,checksums_from_file_dict,args.checksumFile,args.checkCorruption,args.sqLiteFile)
	if args.fileDiff is not None:
            log_info("Writing difference matrix to file "+args.fileDiff)
            diff_file = open(args.fileDiff,'w')
	    diff_file.write(pretty_string(diff,conditions_dict))
	    diff_file.close()
        else:
	    log_info("Pretty printing...")
            print pretty_string(diff,conditions_dict)
        for metric_name in metric_values.keys():
            log_info("Writing values of metric \""+metric_name+"\" to file \""+metrics[metric_name]["output_file"]+"\"")
            metric_file = open(metrics[metric_name]["output_file"],'w')
	    metric_file.write(pretty_string(metric_values[metric_name],conditions_dict))
	    metric_file.close()
	if args.execFile is not None:
	  log_info("Writing executable details to file")
          exec_file = open(args.execFile,'w')
          for key in dictionary_executables:
            executable_details_list=dictionary_executables[key]		
	    if executable_details_list:
	      str_file ="File:"
	      #Below condition is in order to distinguish the intra-condition runs and append ** to the executable details. 
	      if executable_details_list[0] == True:
	        str_file = "**File:"
		#Removing the intra_run_indicator flag
		executable_details_list.pop(0)
            for row in executable_details_list:
	      exec_file.write("\n" + str_file + key + " was used by the process " + row[0] + "\n\n" + "argv:" + row[1] + "\n\n" + "envp:" + row[2] + "\n\n" + "timestamp:" + str(row[3]) +"\n\n" + "working directory:" + row[4] + "\n")
          exec_file.close()

if __name__=='__main__':
	main()

