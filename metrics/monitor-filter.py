#!/usr/bin/env python

import argparse
import hashlib
import logging
import os
import re
import sys

def log_error(message):
    logging.error(message)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Monitor filter is used to find out the differences among the hardware metrics on which the subject folder runs")
    parser.add_argument("first_monitor_text")
    parser.add_argument("second_monitor_text")
    args = parser.parse_args()
    first_monitor_dict={}
    second_monitor_dict={} 
    if os.path.exists(args.first_monitor_text) and os.path.exists(args.second_monitor_text):
      monitor_file_1 = open(args.first_monitor_text, 'r')
      monitor_file_2 = open(args.second_monitor_text, 'r')
      file1_lines = monitor_file_1.readlines()
      file2_lines = monitor_file_2.readlines()
      monitor_file_1.close()
      monitor_file_2.close()
      if not compare_packages(file1_lines)==compare_packages(file2_lines):
	print 1
       

def traverse_file(file_lines):
  monitor_dict={}
  vendor_id_list=[];
  cpu_family_list=[];
  model_name_list=[];
  cpu_mhz_list=[]
  MemTotal=None
  MemFree=None
  #Logic for the processor,memory and system info
  line_data=line.strip().split(':')
  if len(line_data) == 2:
    if "vendor_id\t"==line_data[0]:
      vendor_id_list.append(line_data[1].strip())
    if "cpu family\t"==line_data[0]:
      cpu_family_list.append(line_data[1].strip())
    if "model name\t"==line_data[0]:
      if len(line_data[1].split('@')) == 2:
        model_name=line_data[1].split('@')[0]
        model_name_list.append(model_name.strip())
    if "cpu MHz\t\t"==line_data[0]:
      if len(line_data[1].split('.')) == 2:
        cpu_mhz_list.append(line_data[1].split('.')[0].strip())
    if "MemTotal"==line_data[0]:
      MemTotal=(line_data[1].strip()).split(" ")[0]
    if "MemFree"==line_data[0]:
      MemFree=(line_data[1].strip()).split(" ")[0]
    if "Linux" in line:
      line_data=line.strip().split(" ")
      #print line_data     
	
    #print packages_list
  monitor_dict["memtotal"]=MemTotal
  monitor_dict["memfree"]=MemFree
  monitor_dict["packages"]=packages_list
  monitor_dict["vendor_id"]=vendor_id_list
  monitor_dict["cpu_family"]=cpu_family_list
  monitor_dict["cpu_mhz"]=cpu_mhz_list
  monitor_dict["model_name_list"]=model_name_list

  #print monitor_dict    

def compare_packages(file_lines):
  limit=0
  hasher=hashlib.md5()
  packages_list=[]
  package_flag=True
  for line in file_lines:
    if "List of installed packages" in line:
      package_flag=True
    if "*" in line:
      newline=line.strip().replace("*","")
      if len(newline)==0:
        limit+=1
      if limit>=3:
        package_flag=False
    if package_flag:
      if "*" not in line:
        hasher.update(line.strip())
  return hasher.hexdigest()
        
if __name__=='__main__':
    main()

