import unittest
import verifyFiles
import tempfile
import sys
import os
import shutil
import glob
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


   def testListFilesAndDirs(self):
      listFileAndDirs=[]
      tmpDir=tempfile.mkdtemp()
      tmpListFileAndDirs=[]
      tmpFileName1='myFile1'
      tmpFileName2='myFile2'
      fileDir1=os.path.join(tmpDir,tmpFileName1)
      fileDir2=os.path.join(tmpDir,tmpFileName2)
      try:
         with open(fileDir1, "w") as tmp:
            tmp.write("/home/S1C1\n/home/S2C2\n")
         with open(fileDir2, "w") as tmp:
            tmp.write("/home/S1C1\n/home/S2C2\n")
         listFileAndDirs=verifyFiles.list_files_and_dirs(tmpDir)
         files = glob.glob(tmpDir + "*")
         files.sort(key=lambda x: os.path.getmtime(x))
         #dirs.sort(key=lambda s: os.path.getmtime(os.path.join(tmpDir, s)))
         print files
      except IOError as e:
         print 'IOError'
      else:
         os.remove(fileDir1)
         os.remove(fileDir2)
      finally:
         shutil.rmtree(tmpDir)
      print listFileAndDirs
      self.assertEqual(listFileAndDirs,tmpListFileAndDirs)

  #def testPopulateFileDirDict(self):
  #assert True


if __name__=='__main__':
   unittest.main()
