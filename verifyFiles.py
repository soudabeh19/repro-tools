#!/usr/bin/env python

# #verifyFiles.py
#
# Script to check whether the output files generated across 
# subject folders in different conditions are the same or not.
#

import os
import sys
import subprocess
import argparse,textwrap
import hashlib
import operator
import logging

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
def read_contents_from_file(file_name): 
    with open(file_name, 'r') as infile:
        data=infile.read()  
        directory_list=data.splitlines()
    return directory_list

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

# Returns True if and only if 'path_name' is present in all subjects
# of all conditions in 'conditions_dict'. 'conditions_dict' is the
# dictionary returned by 'get_conditions_dict'.
def is_common_path(conditions_dict,path_name):
    for condition in conditions_dict.keys():
        for subject in conditions_dict[condition].keys():
            if not path_name in conditions_dict[condition][subject].keys():
                print "Under condition",condition, "folder", subject, "is missing the file" , path_name
		return False
    return True
              
# Returns a list of path names that are present in all subjects of all
# conditions in 'conditions_dict'. 'conditions_dict' is the dictionary
# returned by 'get_conditions_dict'.
def common_paths_list(conditions_dict):
    common_paths=[]
    # Iterate over the files in the first subject of the first condition
    first_condition=conditions_dict.keys()[0]
    first_subject=conditions_dict[first_condition].keys()[0]
    for path_name in conditions_dict[first_condition][first_subject].keys():
        if is_common_path(conditions_dict,path_name):
            # Note: in is_common_path we also check if the
            # path is in the first subject of the first
            # condition while this is not necessary
            common_paths.append(path_name)
    return common_paths

# Returns a dictionary where the keys identifies two conditions
# (e.g. "condition1 vs condition2") and the values are dictionaries
# where the keys are path names common to these two conditions and the
# values are the number of times that this path differs among all
# subjects of the two conditions.
# For instance:
#  {'condition1 vs condition2': {'c/c.txt': 0, 'a.txt': 2}}
#  means that 'c/c.txt' is identical for all subjects in conditions condition1 and condition2 while 'a.txt' differs in two subjects.
def n_differences_across_subjects(conditions_dict,common_paths,root_dir):
    # For each pair of conditions C1 and C1
    product = ((i,j) for i in conditions_dict.keys() for j in conditions_dict.keys())
    diff={} # Will be the return value
    # Go through all pairs of conditions
    for c, d in product:
        if c < d: # Makes sure that pairs are not ordered, i.e. {a,b} and {b,a} are the same
            key=c+" vs "+d
            diff[key]={}
            for file_name in common_paths:
                diff[key][file_name]=0
                for subject in conditions_dict[c].keys():
                # Here we assume that both conditions will have the same set of subjects
                    if(conditions_dict[c][subject][file_name].st_size != conditions_dict[d][subject][file_name].st_size):
                        #diff[key][file_name]["binary_content"]+=1
			diff[key][file_name]+=1
                    else:
                        # File sizes are identical: compute the checksums
                        abs_path_c=os.path.join(root_dir,c,subject,file_name)
                        abs_path_d=os.path.join(root_dir,d,subject,file_name)
                        if checksum(abs_path_c) != checksum(abs_path_d): # TODO:when they are multiple conditions, we will compute checksums multiple times.
                                                                         # We should avoid that.
                            #diff[key][file_name]["binary_content"]+=1
			    diff[key][file_name]+=1
                            # if there is a metric or more associated with this file name, compute it here.
                            #diff[key][file_name][metric_name]+= # result of the metric execution
    return diff

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

#Method is_subject_folders_same checks if the subject_folders under different conditions are the same. If not , it stops the execution of the script.
def is_subject_folders_same(conditions_list,root_dir):
   if len(conditions_list) > 1:
      subject_folders_ref_list=[subject_name for subject_name in sorted(os.listdir(os.path.join(root_dir,conditions_list[0]))) if os.path.isdir(os.path.join(root_dir,conditions_list[0],subject_name))]
      if len(subject_folders_ref_list) != 0:
         for condition in conditions_list[1:]:
            subject_folders_list=[]
            for subject_name in sorted(os.listdir(os.path.join(root_dir,condition))):
                if os.path.isdir(os.path.join(root_dir,condition,subject_name)):
                   subject_folders_list.append(subject_name)
            if not are_equal(subject_folders_ref_list, subject_folders_list):
               missing_folder_list = list(set(subject_folders_ref_list) -  set(subject_folders_list))
               if len(missing_folder_list) != 0:
                  print "Subject folder/(s) are not the same in all the conditions.",missing_folder_list,"is missing under condition",os.path.join(root_dir,condition)
               else:
                  missing_folder_list=list(set(subject_folders_list) -  set(subject_folders_ref_list))
                  print "Subject folder/(s) are not the same in all the conditions.",missing_folder_list,"is missing under condition",os.path.join(root_dir,conditions_list[0])
               sys.exit(1)
            
            

def are_equal(subject_list_ref, subject_list_under_condition):
    return set(subject_list_ref) == set(subject_list_under_condition)       
   

# Prints a formatted log. There must be a better way of doing that in Python
def log(message):
    logging.info(message)

def main():
        parser=argparse.ArgumentParser(description="verifyFiles.py", usage="./verifyFiles.py <input_file_name> [-c]",formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("file_in", help= textwrap.dedent('''Input the text file containing the path to the subject folders
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
        parser.add_argument("-c", "--checksumfile",action="store_true",help="Reads checksum from files. Doesn't compute checksums locally")
	parser.add_argument("-d", "--fileDiff", help="Writes the difference matrix into a file") 
        args=parser.parse_args()
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
	conditions_file_name=sys.argv[1]
        conditions_list=read_contents_from_file(conditions_file_name)
        root_dir=os.path.dirname(os.path.abspath(conditions_file_name))
        log("Walking through files...")
        is_subject_folders_same(conditions_list,root_dir)
        conditions_dict=get_conditions_dict(conditions_list,root_dir)
        log("Finding common files across conditions and subjects...")
        common_paths=common_paths_list(conditions_dict)
        log("Computing differences across subjects...")
        diff=n_differences_across_subjects(conditions_dict,common_paths,root_dir)
	if args.fileDiff is not None:
           diff_file = open(args.fileDiff,'w')
	   diff_file.write(pretty_string(diff,conditions_dict))
	   diff_file.close()
        else:
	   log("Pretty printing...")
           print pretty_string(diff,conditions_dict)

if __name__=='__main__':
	main()

