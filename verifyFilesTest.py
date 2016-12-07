import unittest
import verifyFiles
import tempfile,shutil
import sys
import os
import glob
from io import StringIO

#VerifyFilesTest.py contains test cases that verify the correct functionality of the methods in the verifyFiles.py 
#python script file

class VerifyFilesTestCase(unittest.TestCase):
 
   def setUp(self):
      self.test_dir = tempfile.mkdtemp()

   def tearDown(self):
      shutil.rmtree(self.test_dir)

   #Test Case testReadContentsFromFile will test and ensure that read_contents_from_file method
   # is working as expected
   def testReadContentsFromFile(self):
      read_file_content=[]
      filename='myfile'
      path = os.path.join(self.test_dir, filename)
      read_file_content.append("/home/S1C1")
      read_file_content.append("/home/S2C2")
      try:
         with open(path, "w") as tmp:
            tmp.write("/home/S1C1\n/home/S2C2\n")
         directory_list=verifyFiles.read_contents_from_file(path)
      except IOError as e:
         print 'IOError'
      else:
         os.remove(path)
      self.assertEqual(directory_list,read_file_content)


   def testListFilesAndDirs(self):
      tmp_list_files_and_dirs=[]
      file1_dir=os.path.join(self.test_dir, 'file1.txt')
      file2_dir=os.path.join(self.test_dir, 'file2.txt')
      try:
	 tmp_list_files_and_dirs.append('.')
	 tmp_list_files_and_dirs.append('./file1.txt')
	 tmp_list_files_and_dirs.append('./file2.txt')
         file1=open(os.path.join(self.test_dir, 'file1.txt'), 'w')
	 file1.write('The owls are silent')
	 file2=open(os.path.join(self.test_dir,'file2.txt'),'w')
	 file2.write('The owls are wise')
	 list_files_and_dirs=verifyFiles.list_files_and_dirs(self.test_dir)
      except IOError as e:
         print 'IOError'
      else:
         os.remove(file1_dir)
         os.remove(file2_dir)
      self.assertEqual(tmp_list_files_and_dirs,list_files_and_dirs)

  #def testPopulateFileDirDict(self):
  #assert True


if __name__=='__main__':
   unittest.main()
