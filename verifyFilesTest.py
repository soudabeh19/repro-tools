import unittest
import verifyFiles
import tempfile,shutil
import sys
import os
import glob
from collections import defaultdict,OrderedDict
from io import StringIO

#VerifyFilesTest.py contains test cases that verify the correct functionality of the methods in the verifyFiles.py 
#python script file

class VerifyFilesTestCase(unittest.TestCase):
   @classmethod
   def setUpClass(self):
      self.test_dir = tempfile.mkdtemp()
      file1=open(os.path.join(self.test_dir, 'dummy_text.txt'), 'w')
      file1.write('The owls are silent')
      file2=open(os.path.join(self.test_dir,'dummy1_text.txt'),'w')
      file2.write('The owls are wise')
      #Following are the steps to create a subdirectory
      sys_temp = tempfile.gettempdir()
      inner_dir = os.path.join(sys_temp,'inner_dir')
      #You must make sure myTemp exists
      if not os.path.exists(inner_dir):
         os.makedirs(inner_dir)
      #now make your temporary sub folder
      inner_temp_dir = tempfile.mkdtemp(dir=inner_dir)
      inner_file1 = open(os.path.join(inner_temp_dir, 'inner_file.txt'), 'w')
      inner_file1.write('The owls are silent')
   
   @classmethod
   def tearDownClass(self):
      shutil.rmtree(self.test_dir)
	

   #Test Case testReadContentsFromFile will test and ensure that read_contents_from_file method
   # is working as expected
   def test_read_contents_from_file(self):
      read_file_content=[]
      path = os.path.join(self.test_dir, 'file_name')
      read_file_content.append('/home/S1C1')
      read_file_content.append('/home/S2C2')
      try:
         with open(path, 'w') as tmp:
            tmp.write('/home/S1C1\n/home/S2C2\n')
         directory_list=verifyFiles.read_contents_from_file(path)
      except IOError as e:
         print 'IOError'
      else:
         os.remove(path)
      self.assertEqual(directory_list,read_file_content)


   def test_get_dict_with_file_and_dir_attributes(self):
      temp_dict=defaultdict(list)
      try:
	 temp_dict.setdefault('./dummy1_text.txt',[]).append(os.stat(os.path.join(self.test_dir,'dummy1_text.txt')))
         temp_dict.setdefault('./dummy_text.txt',[]).append(os.stat(os.path.join(self.test_dir,'dummy_text.txt')))
         temp_dict.setdefault('.',[]).append(os.stat(os.path.join(self.test_dir,'.')))
	 ordered_dict_from_script=verifyFiles.get_dict_with_file_and_dir_attributes(self.test_dir)
      except IOError as e:
         print 'IOError'
      self.assertEqual(ordered_dict_from_script,OrderedDict(temp_dict))
  
  #def test_retrieve_file_attributes

if __name__=='__main__':
   unittest.main()
