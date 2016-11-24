import unittest
import verifyFiles
import tempfile
import sys
import os
from io import StringIO

#VerifyFilesTest.py contains test cases that verify the correct functionality of the methods in the verifyFiles.py 
#python script file

class VerifyFilesTestCase(unittest.TestCase):
  
   def testReadContentsFromFile(self):
      read_file_content=[]
      tmpdir=tempfile.mkdtemp()
      predictable_filename='myfile'
      path = os.path.join(tmpdir, predictable_filename)
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
      finally:
         os.rmdir(tmpdir)
      self.assertEqual(directory_list,read_file_content)


  #def testListFilesAndDirs(self):
  #assert True

  #def testPopulateFileDirDict(self):
  #assert True


if __name__=='__main__':
   unittest.main()
