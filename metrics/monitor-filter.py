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
      if compare_monitor_files(file1_lines)!=compare_monitor_files(file2_lines):
       	print 1
      else:
	print 0
       
#Method comapre_monitor_files parses the monitor.txt file
#line by line and concatenates the necessary values into a 
#hasher variable which is used to compute the checksum out of the 
#stored values.
def compare_monitor_files(file_lines):
  limit=0
  hasher=hashlib.md5()
  packages_list=[]
  package_flag=True
  for line in file_lines:
    if "List of installed packages" in line:
      package_flag=True
    elif "*" in line:
      newline=line.strip().replace("*","")
      if len(newline)==0:
        limit+=1
      if limit>=3:
        package_flag=False
    if package_flag:
      if "*" not in line:
        hasher.update(line.strip()) #Check if the last line is only computed the checksum.
    line_data=line.strip().split(':')
    if len(line_data) == 2:
      if "processor\t"==line_data[0]:
        hasher.update(line_data[1].strip())
      if "vendor_id\t"==line_data[0]:
        hasher.update(line_data[1].strip())
      if "cpu family\t"==line_data[0]:
        hasher.update(line_data[1].strip())
      if "model name\t"==line_data[0]:
        if len(line_data[1].split('@')) == 2:
          model_name=line_data[1].split('@')[0]
          hasher.update(model_name.strip())
      if "MemTotal"==line_data[0]:
        hasher.update((line_data[1].strip()).split(" ")[0])
    if "Linux" in line:
      line_data=line.strip().split(" ")
      hasher.update(line_data[0]+line_data[2]+line_data[13]+line_data[14])
  return hasher.hexdigest()
        
if __name__=='__main__':
    main()

