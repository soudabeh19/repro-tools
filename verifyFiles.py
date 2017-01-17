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

# Returns a dictionary where the keys are the paths in 'directory'
# (relative to 'directory') and the values are the os.stat objects
# associated with these paths. By convention, keys representing
# directories have a trailing '/'.
def get_dir_dict(directory): 
    result_dict={}
    result_dict['./']=os.stat(directory)
    for root,dirs,files in os.walk(directory):
        for file_name in files:
            abs_file_path=os.path.join(root,file_name)
            rel_path=abs_file_path.replace(os.path.join(directory+"/"),"")
            result_dict[rel_path]=os.stat(abs_file_path)
        for dir_name in dirs:
            abs_path=os.path.join(root,dir_name)
            rel_path=abs_path.replace(os.path.join(directory+"/"),"")+"/"
            result_dict[rel_path]=os.stat(abs_path)
    return result_dict

# Returns a dictionary where the keys are the directories in
# 'condition_dir' and the values are the directory dictionaries (as
# returned by get_dir_dict) associated to these directories.
def get_condition_dict(condition_dir):
    condition_dict={}
    for subject_name in os.listdir(condition_dir):
        subject_dir_path=os.path.join(condition_dir,subject_name)
        if os.path.isdir(subject_dir_path):
            condition_dict[subject_name]=get_dir_dict(subject_dir_path)
    return condition_dict

# Returns a dictionary where the keys are the names in
# 'condition_names' and the values are the corresponding condition
# dictionaries (as returned by get_condition_dict)
def get_conditions_dict(condition_names,root_dir):
    conditions_dict={}
    for condition in condition_names:
        conditions_dict[condition]=get_condition_dict(os.path.join(root_dir,condition))
    return conditions_dict

# Returns a list where each element is a line in 'file_name'
def read_conditions_file(file_name): 
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
                    log_error("File \"" + path_name  + "\" is missing in subject \"" + subject + "\" of condition \"" + condition+"\".")

# Returns a dictionary where the keys identifies two conditions
# (e.g. "condition1 vs condition2") and the values are dictionaries
# where the keys are path names common to these two conditions and the
# values are the number of times that this path differs among all
# subjects of the two conditions.
# For instance:
#  {'condition1 vs condition2': {'c/c.txt': 0, 'a.txt': 2}}
#  means that 'c/c.txt' is identical for all subjects in conditions condition1 and condition2 while 'a.txt' differs in two subjects.
def n_differences_across_subjects(conditions_dict,root_dir,metrics):
    # For each pair of conditions C1 and C1
    product = ((i,j) for i in conditions_dict.keys() for j in conditions_dict.keys())
    diff={} # Will be the return value
    metric_values={}
    path_names = conditions_dict.values()[0].values()[0].keys()
    # Go through all pairs of conditions
    for c, d in product:
        if c < d: # Makes sure that pairs are not ordered, i.e. {a,b} and {b,a} are the same
            key=c+" vs "+d
            diff[key]={}
            for file_name in path_names:
                diff[key][file_name]=0
                for subject in conditions_dict[c].keys():
                # Here we assume that both conditions will have the same set of subjects
                    files_are_different=False
                    if(conditions_dict[c][subject][file_name].st_size != conditions_dict[d][subject][file_name].st_size):
                        #diff[key][file_name]["binary_content"]+=1
			diff[key][file_name]+=1
                        files_are_different=True 
                    else:
			abs_path_c=os.path.join(root_dir,c,subject,file_name)
                        abs_path_d=os.path.join(root_dir,d,subject,file_name)
                        # File sizes are identical: compute the checksums
	                if checksums_flag:
                            folder_c_checksums_file=os.path.join(root_dir,c,subject,"checksums-after.txt")
			    folder_d_checksums_file=os.path.join(root_dir,d,subject,"checksums-after.txt")
			    #print folder_c_checksums_file,folder_d_checksums_file
                            if os.path.isfile(folder_c_checksums_file) and os.path.isfile(folder_d_checksums_file):
    			        if not is_checksum_equal(folder_c_checksums_file,folder_d_checksums_file,subject,file_name):
				    diff[key][file_name]+=1
                                    files_are_different=True                            
                        elif checksum(abs_path_c) != checksum(abs_path_d): # TODO:when they are multiple conditions, we will compute checksums multiple times.We should avoid that.
			    diff[key][file_name]+=1
                            files_are_different=True
                    if files_are_different:
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
    return diff,metric_values

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
        log_error("Command "+command+" failed.")
    return output


#Method is_checksum_equal reads the checksum
#and returns true if the checksums are matching.
def is_checksum_equal(checksums_after_file_condition1,checksums_after_file_condition2,subject,file_name):
    file_dir = "./"+subject+"/"+file_name
    checksum_second_file = None
    checksum_first_file = None
    with open(checksums_after_file_condition1) as file1:
        for line in file1:
            if file_dir in line:
	        checksum_first_file = line.split(' ', 1)[0]
    
    with open(checksums_after_file_condition2) as file2:
        for line in file2:
	    if file_dir in line:
                checksum_second_file = line.split(' ',1)[0]
    
    return checksum_second_file==checksum_first_file and (checksum_second_file != None and checksum_first_file != None)

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
        args=parser.parse_args()
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
	conditions_file_name=args.file_in
        conditions_list=read_conditions_file(conditions_file_name)
        root_dir=os.path.dirname(os.path.abspath(conditions_file_name))
        log_info("Walking through files...")
	global checksums_flag
	checksums_flag = False
	if args.checksumFile is not None:
            checksums_flag = True
        conditions_dict=get_conditions_dict(conditions_list,root_dir)
        log_info("Checking if subject folders are missing in any condition...")
	check_subjects(conditions_dict)
	log_info("Checking if files are missing in any subject of any condition...")
        check_files(conditions_dict)
        log_info("Reading the metrics file...")
        metrics = read_metrics_file(args.metricsFile)
        log_info("Computing differences across subjects...")
        diff,metric_values=n_differences_across_subjects(conditions_dict,root_dir,metrics)
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

if __name__=='__main__':
	main()

