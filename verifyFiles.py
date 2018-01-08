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
import pandas as pd
import random
# Returns a dictionary where the keys are the paths in 'directory'
# (relative to 'directory') and the values are the os.stat objects
# associated with these paths. By convention, keys representing
# directories have a trailing '/'.
def get_dir_dict(directory,exclude_items): 
    result_dict={}
    for root,dirs,files in os.walk(directory):
	if exclude_items is not None:
	    dirs[:]=[d for d in dirs if d not in exclude_items]
	    #To eliminate the files listd in exclude items file. Condition below checks relative file path as well as file names. 
            files[:]=[f for f in files if f not in exclude_items and os.path.join(root,f).replace(os.path.join(directory+"/"),"") not in exclude_items]
        for file_name in files:
	    if not exclude_items or (file_name not in exclude_items):
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
                    log_warning("File \"" + path_name  + "\" is missing in subject \"" + subject + "\" of condition \"" + condition + "\".")

# Returns a dictionary where the keys identifies two conditions
# (e.g. "condition1 vs condition2") and the values are dictionaries
# where the keys are path names common to these two conditions and the
# values are the number of times that this path differs among all
# subjects of the two conditions.
# For instance:
#  {'condition1 vs condition2': {'c/c.txt': 0, 'a.txt': 2}}
#  means that 'c/c.txt' is identical for all subjects in conditions condition1 and condition2 while 'a.txt' differs in two subjects.
def n_differences_across_subjects(conditions_dict,root_dir,metrics,checksums_from_file_dict,checksum_after_file_path,check_corruption,sqlite_db_path,track_processes):
    # For each pair of conditions C1 and C1
    product = ((i,j) for i in conditions_dict.keys() for j in conditions_dict.keys())
    diff={} # Will be the return value
    bDiff={} # will be the return value for being used in binary matrix
    metric_values={}
    # Dictionary_modtime is used for sorting files by increasing modification time for each subject in each condition 
    modtime_dict={}
    for key in conditions_dict.keys():
	modtime_dict[key]={}
	for subject in conditions_dict.values()[0].keys():
            mtime_list=[]
	    modtime_dict[key][subject]={}
	    for path_name in conditions_dict.values()[0].values()[0].keys(): 
  	        mtime_list.append((path_name,conditions_dict[key][subject][path_name].st_mtime))
	    modtime_dict[key][subject]= sorted(mtime_list, key=lambda x: x[1])  
    #Dictionary metric_values_subject_wise holds the metric values mapped to individual subjects. 
    #This helps us identify the metrics values and associate it with individual subjects.
    metric_values_subject_wise={}
    path_names = conditions_dict.values()[0].values()[0].keys()
    #dictionary_checksum is used for storing the computed checksum values and to avoid computing the checksums for the files multiple times
    dictionary_checksum={}
    #dictionary_executables is used for tracking the files that we have already found the executables for
    dictionary_executables={}
    dictionary_processes={}
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
            bDiff[key]={}
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
            for subject in conditions_dict[c].keys():
		bDiff[key][subject]={}
		for file_name in path_names:
		    bDiff[key][subject][file_name]={}
            for file_name in path_names:
		diff [key][file_name]=0
                for subject in conditions_dict[c].keys():
                # Here we assume that both conditions will have the same set of subjects
	            files_are_different=False
		    abs_path_c=os.path.join(root_dir,c,subject,file_name)
                    abs_path_d=os.path.join(root_dir,d,subject,file_name)
		    # Random selection of modtime_list of subject between two conditions
		    selected_condition=random.choice([c,d])
		    for key_name in modtime_dict:
		        if key_name == selected_condition: 
		           mtime_files_list = modtime_dict[key_name][subject]
		           bDiff[key][subject]['mtime_files_list'] = mtime_files_list
		    
                    if checksums_from_file_dict: 
		      if (checksums_from_file_dict[c][subject][file_name] != checksums_from_file_dict[d][subject][file_name]):
                        files_are_different=True
		    elif conditions_dict[c][subject][file_name].st_size != conditions_dict[d][subject][file_name].st_size :
		        files_are_different=True
		    else:
		      #Computing the checksum if not present in the dictionary and adding it to the dictionary to avoid multiple checksum computation.                   
		      for filename in {abs_path_d,abs_path_c}:
                        if filename not in dictionary_checksum:
                          dictionary_checksum[filename] = checksum(filename)
                      if dictionary_checksum[abs_path_c] != dictionary_checksum[abs_path_d]:
                        files_are_different=True

		    #Track the processes which created the files using reprozip trace.
		    if track_processes and sqlite_db_path and file_name not in dictionary_processes and file_name.endswith("nii.gz") :
		       dictionary_processes[file_name]=get_executable_details(conn,sqlite_db_path,file_name)    
		    
                    if files_are_different:
			diff[key][file_name]+=1
  			bDiff[key][subject][file_name]=1		
	
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
                                if metric['name'] not in metric_values.keys() and metric['name'] not in metric_values_subject_wise.keys():
                                    metric_values[metric['name']]={}
				    metric_values_subject_wise[metric['name']]={}
                                if key not in metric_values[metric['name']].keys() and key not in metric_values_subject_wise[metric['name']].keys():
                                    metric_values[metric['name']][key] = {}
				    metric_values_subject_wise[metric['name']][key]={}
				#To add subject along with the file name to identify individual file differences
				if subject not in metric_values_subject_wise[metric['name']][key].keys():
				    metric_values_subject_wise[metric['name']][key][subject]={}
                                if file_name not in metric_values[metric['name']][key].keys() and file_name.endswith(metric['extension']):
				    metric_values[metric['name']][key][file_name]=0
				if file_name not in metric_values_subject_wise[metric['name']][key][subject].keys() and file_name.endswith(metric['extension']):
				    metric_values_subject_wise[metric['name']][key][subject][file_name]= 0
				if file_name.endswith(metric['extension']):
				    try:
					log_info("Computing the metrics for the file:"+" "+file_name+" "+"in subject"+" "+subject)
					log_info(file_name +" "+ c +" "+ d +" "+ subject +" "+ metric['command'])
                                        diff_value=float(run_command(metric['command'],file_name,c,d,subject,root_dir))
					metric_values[metric['name']][key][file_name] += diff_value
					metric_values_subject_wise[metric['name']][key][subject][file_name] = diff_value
				    except ValueError as e:
					log_error("Result of metric execution could not be cast to float"+" "+metric['command']+" "+file_name+" "+c+" "+d+" "+subject+" "+root_dir)
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
	            else:
                        bDiff[key][subject][file_name]=0
	
    if sqlite_db_path:
      conn.close()
    return diff,bDiff,metric_values,dictionary_executables,dictionary_processes,metric_values_subject_wise

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
# 'command condition1/subject_name/file_name condition2/subject_name/file_name'
# and returns the stdout if and only if command was successful
def run_command(command,file_name,condition1,condition2,subject_name,root_dir):
    command_string = command+" "+os.path.join(root_dir,condition1,subject_name,file_name)+" "+os.path.join(root_dir,condition2,subject_name,file_name)+" "+"2>/dev/tty"
    return_value,output = commands.getstatusoutput(command_string)
    if return_value != 0:
        log_error(str(return_value)+" "+ output +" "+"Command "+ command + " failed (" + command_string + ").")
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
#Write column_index text file of the matrix 
def matrix_column(bDiff,condition,condition_id,column_index):
    column_index.write(str(condition_id))
    column_index.write(";")
    column_index.write(str(condition))
    column_index.write("\n")
#Write the text file of matrix according to the define conditions for it
def matrix_differences(bDiff,condition,subject,path,r,c,mode,differences):
    differences.write(str(r))
    differences.write(";")
    differences.write(str(c))
    differences.write(";")
    if mode == True:
    	differences.write(str(bDiff[condition][subject][path]))
    	differences.write(";")
    	differences.write(str([bDiff[condition][subject]['mtime_files_list'].index(t) for t in bDiff[condition][subject]['mtime_files_list'] if t[0] == path])[1:-1]) # file_index
    else:
        differences.write(str(bDiff[condition][subject][path]))
    differences.write("\n")
#Write row_index text file of the matrix    
def matrix_row(bDiff,subject,path,r,mode,row_index):
    row_index.write(str(r))
    row_index.write(";")
    if mode == False:
        row_index.write(str(subject))
        row_index.write(";")
    row_index.write(str(path))
    row_index.write("\n")
#Write binary_difference_matrix 
def matrix_text_files(bDiff,conditions_dict,fileDiff,mode,condition_pairs):
    r=0
    c=0
    if mode == True:
        file_name = "_2D_"+str(condition_pairs)
        file_name = file_name.replace(' ', '').replace("/","_")
    else:
	file_name = "_3D"
    row_index = open(fileDiff + file_name + "_row_index.txt","w+")
    column_index = open(fileDiff + file_name + "_column_index.txt","w+")
    differences = open(fileDiff + file_name + "_differences.txt","w+")
    if mode == True:
	for subject in bDiff[bDiff.keys()[0]].keys():
	    matrix_column(bDiff,subject,c,column_index) 
	    for path in conditions_dict.values()[0].values()[0].keys():
		matrix_differences(bDiff,condition_pairs,subject,path,r,c,mode,differences)
                matrix_row(bDiff,subject,path,r,mode,row_index)
		r+=1
	    r=0
	    c+=1
    else:
	for condition in bDiff.keys():
            matrix_column(bDiff,condition,c,column_index)
            for subject in bDiff[bDiff.keys()[c]].keys():
                for path in conditions_dict.values()[c].values()[c].keys():
		    matrix_differences(bDiff,condition,subject,path,r,c,mode,differences)
		    matrix_row(bDiff,subject,path,r,mode,row_index)
		    r+=1
            r=0
            c+=1
    return (row_index,column_index,differences)

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
	    if comparison in diff_dict and path in diff_dict[comparison]:
	      value=str(diff_dict[comparison][path])
	    else:
	      value="0"
            output_string+=value
            for i in range(1,max_comparison_key_length/2+1):
                output_string+=" "
            output_string+="\t"
        output_string+="\n"
    return output_string

# Returns a string containing a 'pretty' matrix representation of the
# dictionary returned by n_differences_across_subjects
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



#function to write the individual file detials to files
def write_filewise_details(metric_values_subject_wise,metric_name,file_name):
      log_info(metric_name + " values getting written to subject wise into a csv file: " + file_name)
      with open(file_name, 'wb') as f:
       writer = csv.writer(f)
       for item in metric_values_subject_wise[metric_name]:
        for subject in metric_values_subject_wise[metric_name][item]:
         for file_name in metric_values_subject_wise[metric_name][item][subject]:
	  writer.writerow([item,subject,file_name,metric_values_subject_wise[metric_name][item][subject][file_name]])
    
# Logging functions

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error("ERROR: " + message)
    sys.exit(1)

def log_warning(message):
    logging.warning("WARNING: "+message)
    
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
	parser.add_argument("result_base_name", help='''Base name to use in output file names. The following files will be written: 
			   <result_base_name>_differences_subject_total.txt: Total sum of differences for each file among all subjects,
			   <result_base_name>_column_index.txt: List of all indexed condition pairs,
			   <result_base_name>_row_index.txt: List of all indexed pair of subject and file;called as Row,
			   <result_base_name>_differences.txt: Difference value in a file according to its subject and condition pair; display format: row_index.txt, column_index,difference binary value''')
        parser.add_argument("output_folder_name", help="Directory to which all the output files are getting written")
	parser.add_argument("-c", "--checksumFile",help="Reads checksum from files. Doesn't compute checksums locally")
        parser.add_argument("-m", "--metricsFile", help="CSV file containing metrics definition. Every line contains 4 elements: metric_name,file_extension,command_to_run,output_file_name") 
        parser.add_argument("-e","--excludeItems",help="The list of items to be ignored while parsing the files and directories")
	parser.add_argument("-k","--checkCorruption",help="If this flag is kept 'TRUE', it checks whether the file is corrupted")
	parser.add_argument("-s","--sqLiteFile",help="The path to the sqlite file which is used as the reference file for identifying the processes which created the files")
	parser.add_argument("-x","--execFile",help="Writes the executable details to a file")
	parser.add_argument("-t","--trackProcesses",help="Writes all the processes that create an nii file is written into file name mentioned after the flag")	
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
        #diff,metric_values,dictionary_executables,dictionary_processes=n_differences_across_subjects(conditions_dict,root_dir,metrics,checksums_from_file_dict,args.checksumFile,args.checkCorruption,args.sqLiteFile)i
	diff,bDiff,metric_values,dictionary_executables,dictionary_processes,metric_values_subject_wise=n_differences_across_subjects(conditions_dict,root_dir,metrics,checksums_from_file_dict,args.checksumFile,args.checkCorruption,args.sqLiteFile,args.trackProcesses)
       	if args.result_base_name is not None and args.output_folder_name is not None:
            log_info("Writes the difference matrices and indexes into files")
            #Checks if the output folder already exists or not, and creates if it doesn't exist
	    if not os.path.exists(args.output_folder_name):
                os.makedirs(args.output_folder_name)
	    #output_base_path gives the base path with the following format - <output folder path/result_base_name>
	    output_base_path=args.output_folder_name+"/"+args.result_base_name
            diff_file = open(output_base_path+"_differences_subject_total.txt",'w')
            diff_file.write(pretty_string(diff,conditions_dict))
	   # write_text_files (bDiff,conditions_dict,args.result_base_name)
           # two_dimensional_matrix (bDiff,conditions_dict,args.result_base_name)
	    for condition_pairs in bDiff.keys():
                matrix_text_files (bDiff,conditions_dict,output_base_path,True,condition_pairs)# 2D matrix
	    matrix_text_files (bDiff,conditions_dict,output_base_path,False,None)# 3D matrix
            diff_file.close()

        for metric_name in metric_values.keys():
            log_info("Writing values of metric \""+metric_name+"\" to file \""+metrics[metric_name]["output_file"]+"\"")
            metric_file = open(metrics[metric_name]["output_file"],'w')
	    metric_file.write(pretty_string(metric_values[metric_name],conditions_dict))
            if metric_name in metric_values_subject_wise.keys() and args.filewiseMetricValue:
              write_filewise_details(metric_values_subject_wise,metric_name,args.output_folder_name+"/"+metric_name+".csv")
	    metric_file.close()
	
	if args.execFile is not None:
	  log_info("Writing executable details to csv file")
	  with open(args.output_folder_name+"/"+args.execFile, 'wb') as csvfile:
	    fieldnames = ['File Name', 'Process','ArgV','EnvP','Timestamp','Working Directory']
	    writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
	    writer.writeheader()
            for key in dictionary_executables:
              executable_details_list=dictionary_executables[key]
              for row in executable_details_list:
		#Replacing the space character 
		arguments=str(row[1]).replace("\x00"," ")
		envs=str(row[2]).replace("\x00"," ")
	        writer.writerow({'File Name':key, 'Process':row[0],'ArgV':arguments,'EnvP':envs,'Timestamp':row[3],'Working Directory':row[4]})
		csvfile.flush()
	
	if dictionary_processes and args.trackProcesses:
          log_info("Writing process details to csv file named: "+args.trackProcesses)
          with open(args.output_folder_path+"/"+args.trackProcesses, 'wb') as csvfile:
            fieldnames = ['File Name', 'Process','ArgV','EnvP','Timestamp','Working Directory']
            writer=csv.DictWriter(csvfile,fieldnames=fieldnames)
            writer.writeheader()
            for key in dictionary_processes:
              executable_details_list=dictionary_processes[key]
              for row in executable_details_list:
                #Replacing the space character 
                arguments=str(row[1]).replace("\x00"," ")
                envs=str(row[2]).replace("\x00"," ")
                writer.writerow({'File Name':key, 'Process':row[0],'ArgV':arguments,'EnvP':envs,'Timestamp':row[3],'Working Directory':row[4]})
                csvfile.flush()  
	 

if __name__=='__main__':
	main()

