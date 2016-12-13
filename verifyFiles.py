#!/usr/bin/env python

# #verifyFiles.py
#
#Script to check whether the output files generated across 
#subject folders in different conditions are the same or not.
#The conditions on which the script will check the match between two files are 
#filename, size, content, modification time, distance etc.
#
#
#
#
# ##Maintainters
#
# * Big Data Lab Team, Concordia University.
# * email : tristan.glatard@concordia.ca, laletscaria@yahoo.co.in
#
#

import os
import sys
import subprocess
import argparse,textwrap
import hashlib
from collections import defaultdict,OrderedDict
import operator

#get_dict_with_file_and_dir_attributes reads the files and directories inside each directory recursively.
#It collects the details like size, modificaiton time, access time etc.
#These details are saved as a value and each relative file or directory name is used as the key value. 
#The return type of the function is an ordered dictionary containing a list of dictionaries sorted on the 
#basis of modification time(st_mtime) of the the file listed as the key value.
#Input parameter : path_to_the_file_with_conditions_list
def get_dict_with_file_and_dir_attributes(folder_path):
	temp_dict=defaultdict(list)
	for dir_, _, files in os.walk(folder_path):
           temp_dict.setdefault(os.path.relpath(dir_,folder_path), []).append(os.stat(dir_))
	   for file_name in files:
              rel_file=os.path.join(os.path.relpath(dir_,folder_path), file_name)
	      temp_dict.setdefault(rel_file, []).append(os.stat(os.path.join(dir_,file_name)))
	return OrderedDict(sorted(temp_dict.items(), key=lambda t:t[1][0].st_mtime))
	      
	


#Method populate_study_folder_dict will store the details regarding each subject 
#folder in an ordered python dictionary. 
#
#Key : Folder or file name , Value : dictionary with details of the key value
def populate_study_folder_dict(file_path):
	list_of_dictionaries_based_on_conditions=[]
	#study_folders_list : List contains path to the folders contianing 
	#the study folders based on each condition and os
	study_folders_list=read_contents_from_file(file_path)
	for folder in study_folders_list:
           temp_study_folder_dict=OrderedDict()
	   temp_study_folder_dict[folder]=get_dict_with_file_and_dir_attributes(folder_path)
	   list_of_dictionaries_based_on_conditions.append(temp_study_folder_dict)
	return list_of_dictionaries_based_on_conditions

#read_contents_from_file method is used to read the directory path containing the subject folders
#
#Input parameter: file containing directory paths as its content
def read_contents_from_file(file_with_dir_details): 
# Open the file for reading.
	with open(file_with_dir_details, 'r') as infile:
	   data=infile.read()  # Read the contents of the file into memory.
	   #Return a list of the lines, breaking at line boundaries.
	   directory_list=data.splitlines()
	return directory_list

#Method generate_checksum is used for generating checksum of individual files and directories
#present in each subject folder
#
#Input parameters: root directory path , individual file name
def generate_checksum(root_dir, file_name):
        hasher=hashlib.md5()
        if os.path.isfile(os.path.join(root_dir, file_name)):
            md5_sum=file_hash(hasher,os.path.join(root_dir, file_name))
	elif os.path.isdir(os.path.join(root_dir, file_name)):
            md5_sum=directory_hash(hasher,os.path.join(root_dir, file_name))
	return md5_sum

#Method file_hash is used for generating md5 checksum of a file 
#
#Input parameters: file name and hasher
def file_hash(hasher,file_name):
    file_content=open(file_name)
    while True:
        read_buffer=file_content.read(2**20)
        if len(read_buffer)==0: 
	   break
        hasher.update(read_buffer)
    file_content.close()
    return hasher.hexdigest()

#Method directory_hash collects the directory and file names from the directory given as input.
#Checksum is created on the basis of filenames and directories present in the file input directory.
#
#Input parameters: hashed content , path 
def directory_hash(hasher, dir_path):
    if os.path.isdir(dir_path):
        for entry in sorted(os.listdir(dir_path)):
            hasher.update(entry)
    return hasher.hexdigest()

#Method generate_common_files_list will create a list containing the common elements from the 
#different dictionaries corresponding to the conditions in which it was created
#
#Input parameters: dictionary with details of files in each study folder , conditions_list
def generate_common_files_list(study_folder_details_dict_list,conditions_list):
	common_files_list=[]
	conditions_list=list(set().union(*(study_folder_details_dict.keys() for study_folder_details_dict in study_folder_details_dict_list)))
	index=0
	common_set=set()
	#reference_dict is the dictionary which we take as a reference for ordering the list according 
	#to the modification time. From the list the dictionary according to condition S1C1 is by default taken as reference.
	reference_dict=study_folder_details_dict_list[index]
	#reference_set is the set with the list of keys present in the reference dictionary. The keys here will
	#be the absolute file name eg:"100307/T1w/T1w_acpc_dc.nii.gz"
	reference_set=set(reference_dict[conditions_list[0]].keys())
        common_set=reference_set
	for condition_dict in study_folder_details_dict_list:
              dictionary=condition_dict[conditions_list[index]]
	      keys_from_each_dictionary=set(dictionary.keys())
	      common_set=common_set & keys_from_each_dictionary
	      index+=1
	#The union of all the files present in all the folders under different conditions
	common_files_list=list(common_set)
    	return common_files_list

#Method generate_missing_files will create a list containing the files 
#that are not common to all the subject folders processed under various conditions. 
#
#Input parameters: study_folder_details_dict_list,conditions_list and common_files_list
def generate_missing_files_list(study_folder_details_dict_list,conditions_list,common_files_list):
	missing_files_list=[]
	index=0;
	keys_from_all_files=set()
	for condition_dict in study_folder_details_dict_list:
	     dictionary=condition_dict[conditions_list[index]]
	     keys_from_individual_files=set(dictionary.keys())
             #set union(|) to join all the values between a set of keys 
	     keys_from_all_files=keys_from_all_files | keys_from_individual_files
	     index+=1
	#Missing files list is the files remaining when the common list of files is removed from the list of all the
	#files processed under different conditions.
	missing_files_list=list(keys_from_all_files - set(common_files_list))
	return missing_files_list
	     

def main():
        parser=argparse.ArgumentParser(description='verifyFiles.py', usage='./verifyFiles.py <input_file_name>',formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('file_in', help= textwrap.dedent('''Input the text file containing the path to the subject folders
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
        args=parser.parse_args()
        #study_folder_details_dict_list is a list for storing ordered dictionaries 
	#containing the details regarding the files of  individual subjects. Each condition 
        #is a key and subject folder details are its conditions.
	study_folder_details_dict_list=[]
	file_with_conditions_list=sys.argv[1]
        study_folder_details_dict_list=populate_study_folder_dict(file_with_conditions_list)
        conditions_list=list(set().union(*(study_folder_details_dict.keys() for study_folder_details_dict in study_folder_details_dict_list)))
        common_files=generate_common_files_list(study_folder_details_dict_list,conditions_list)
	missing_files=generate_missing_files_list(study_folder_details_dict_list,conditions_list,common_files)
	print "*******************Common Files**********************"
	print common_files
        print "*******************Missing Files**********************"
	print missing_files
	#print study_folder_details_dict_list

if __name__=='__main__':
	main()
