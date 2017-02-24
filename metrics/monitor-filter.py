#!/usr/bin/env python

import argparse
import logging
import sys

def log_error(message):
    logging.error(message)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Monitor filter is used to find out the differences among the hardware metrics on which the subject folder runs")
    parser.add_argument("first_monitor_text")
    parser.add_argument("second_monitor_text")
    args = parser.parse_args()
    
    
        

    


    
if __name__=='__main__':
    main()

