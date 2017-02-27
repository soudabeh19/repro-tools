#!/usr/bin/env python

import argparse
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
      package_flag=False
      limit=0
      newline=""
      packages_list=[]
      for line in file1_lines:
        if "List of installed packages" in line:
	  package_flag=True
	if "*" in line:
	  #print line
          newline=line.strip().replace("*","")
	  #print "replaced:",newline
	  #print "lenth",len(newline)
	  if len(newline)==0:
	    limit+=1
	if limit>=3:
	  package_flag=False
	if package_flag:
	 if "*" not in line:
	   packages_list.append(line.strip())
      print packages_list
      first_monitor_dict["packages"]=packages_list
      print first_monitor_dict
	
      monitor_file_1.close()
      monitor_file_2.close()
      print 1
    
        
if __name__=='__main__':
    main()

