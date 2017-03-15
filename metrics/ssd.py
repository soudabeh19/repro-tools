#!/usr/bin/env python

import argparse
import logging
import nibabel
import sys

def log_error(message):
    logging.error(message)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Computes the Sum of Squared differences between two images.")
    parser.add_argument("first_image_file")
    parser.add_argument("second_image_file")
    args = parser.parse_args()
    
    # Load images using nibabel
    im1 = nibabel.load(args.first_image_file)
    im2 = nibabel.load(args.second_image_file)
        
    # Check that both images have the same dimensions
    shape1 = im1.header.get_data_shape()
    shape2 = im2.header.get_data_shape()
    if shape1 != shape2:
        log_error("Images don't have the same shape!")

    data1 = im1.get_data()
    data2 = im2.get_data()
    
    xdim = shape1[0]
    ydim = shape1[1]
    zdim = shape1[2]
    ssd=0
    if len(shape1) == 4:
      tdim = shape1[3]
      # Go through all the voxels and get the SSD
      for x in range(0,xdim):
            for y in range(0,ydim):
              for z in range(0,zdim):
                  for t in range(0,tdim):
                      ssd += (data1[x][y][z][t]-data2[x][y][z][t])**2
    else:
      for x in range(0,xdim):
          for y in range(0,ydim):
              for z in range(0,zdim):
                  ssd += (data1[x][y][z]-data2[x][y][z])**2

    # That's it!
    print ssd
    
if __name__=='__main__':
    main()
