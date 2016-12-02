#!/usr/bin/env python

# #verifyFiles.py
#
#Script to check whether the output files generated across different 
#conditions are the same or not.
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

#study_folder_details_dict_list is a list for storing ordered dictionaries 
#containing the details regarding the files of  individual subjects.
study_folder_details_dict_list=[]

#Method list_files_and_dirs is used for listing files and directories 
#present in the input directory recursively.And it returns a list of files 
#ordered by modification time.
#
#Input parameter : Directory Path
def list_files_and_dirs(dir_path):
        list_files_and_dirs=[]
        for dir_, _, files in os.walk(dir_path):
           list_files_and_dirs.append(os.path.relpath(dir_,dir_path))
           for file_name in files:
              rel_dir=os.path.relpath(dir_,dir_path)
              rel_file=os.path.join(rel_dir, file_name)
              list_files_and_dirs.append(rel_file)
	#Sort the files and subdirectories according to the modification time.
	list_files_and_dirs.sort(key=lambda x: os.path.getmtime(os.path.join(dir_path,x)))
        return list_files_and_dirs

#Method retrieve_file_attributes returns an ordered  python dictionary 
#to save the status details of
#each file and directory present in the list_files_and_dirs list
#
#Input parameter : List contianing the details of the path of each file and directory.
def retrieve_file_attributes(list_files_and_dirs,dir_path):
        temp_dict=OrderedDict(defaultdict(list))
        for rel_path in list_files_and_dirs:
	   md5_digest=generate_checksum(dir_path,rel_path)
           dir_details=os.stat(os.path.join(dir_path,rel_path))
	   temp_dict.setdefault(rel_path, []).append(md5_digest)
	   temp_dict.setdefault(rel_path, []).append(dir_details)
        return temp_dict

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
	   file_names_and_dir_array=list_files_and_dirs(folder)
	   temp_study_folder_dict[folder]=retrieve_file_attributes(file_names_and_dir_array,folder)
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

#Method generate_checksum is used for generating checksum of individual files.
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

#Method directory_hash recursively traverses in case a directory is found.
#Then it sorts the contents and creates checksum on the entire read content.
#
#Input parameters: hashed content , path 
def directory_hash(hasher, dir_path):
    if os.path.isdir(dir_path):
        for entry in sorted(os.listdir(dir_path)):
            directory_hash(hasher, os.path.join(dir_path, entry))
    elif os.path.isfile(dir_path):
        hasher.update(file_hash(hasher,dir_path))
    else: pass
    return hasher.hexdigest()

#Method generate_common_files_list will create a list containing the common elements from the 
#different dictionaries corresponding to the conditions in which it was created
#
#Input parameters: dictionary with details of files in each study folder , file containing details of directories in each condition
def generate_common_files_list(study_folder_details_dict_list,file_with_directory_details):
	common_files_list=[]
	keys_list=read_contents_from_file(file_with_directory_details)
	index=0
	common_set=set()
	#reference_dict is the dictionary which we take as a reference for ordering the list according 
	#to the modification time. From the list the dictionary according to condition S1C1 is by default taken as reference.
	reference_dict=study_folder_details_dict_list[index]
	#reference_set is the set with the list of keys present in the reference dictionary. The keys here will
	#be the absolute file name eg:"100307/T1w/T1w_acpc_dc.nii.gz"
	reference_set=set(reference_dict[keys_list[0]].keys())
	for item in study_folder_details_dict_list:
              dictionary=item[keys_list[index]]
	      keys_from_each_dictionary=set(dictionary.keys())
	      #if common set is empty
	      if not common_set:
		 #set intersection(&) to find out the common values between a set of keys
	         common_set=reference_set & keys_from_each_dictionary
	      else:
		 common_set=common_set & keys_from_each_dictionary
	      index+=1
	common_files_list=list(common_set)
    	return common_files_list

#Method generate_missing_files will create a list containing the files 
#that are not common to all the subject folders. 
#
#Input parameters: study_folder_details_dict_list,file_with_directory_details and common_files_list
def generate_missing_files_list(study_folder_details_dict_list,file_with_directory_details,common_files_list):
	missing_files_list=[]
	keys_list=read_contents_from_file(file_with_directory_details)
	index=0;
	keys_from_all_files=set()
	for item in study_folder_details_dict_list:
	     dictionary=item[keys_list[index]]
	     keys_from_individual_files=set(dictionary.keys())
             #set union(|) to join all the values between a set of keys 
	     keys_from_all_files=keys_from_all_files | keys_from_individual_files
	     index+=1
	missing_files_list=list(keys_from_all_files - set(common_files_list))
	return missing_files_list
	     

def main():
        parser=argparse.ArgumentParser(description='verifyFiles.py', usage='./verifyFiles.py <input_file_name>',formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('file_in', help= textwrap.dedent('''Input the text file containing the path to the subject folders
                                             Each directory contains subject folders which contains the output processed under different conditions
                                             An example would be a directory containing the files processed using CentOS6 operating system and PreFreeSurfer version 5.0.6
                                             Sample of the input file
                                             /home/$(USER)/CentOS6.FSL5.0.6
                                             /home/$(USER)/CentOS7.FSL5.0.6
                                             Each directory will contain subject folders like 100307,100308 etc'''))
        args=parser.parse_args()
        study_folder_details_dict_list=populate_study_folder_dict(sys.argv[1])
        common_files=generate_common_files_list(study_folder_details_dict_list,sys.argv[1])
	missing_files=generate_missing_files_list(study_folder_details_dict_list,sys.argv[1],common_files)
	print "*******************Common Files**********************"
	print common_files
        print "*******************Missing Files**********************"
	print missing_files
	#print study_folder_details_dict_list

if __name__=='__main__':
	main()
