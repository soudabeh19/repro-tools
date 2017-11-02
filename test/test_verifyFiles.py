import os
import pytest
import commands
import filecmp
from verifyFiles import get_dir_dict
from verifyFiles import checksum 
from verifyFiles import read_file_contents
from verifyFiles import get_conditions_dict
from verifyFiles import get_conditions_checksum_dict

def test_checksum():
  assert checksum("test/condition4") == "45a021d9910102aac726dd222a898334"

def test_dir_dict(tmpdir):
  assert get_dir_dict("test/condition4","test/exclude_items.txt")

def test_conditions_dict():
  conditions_dict = get_mock_conditions_dict()
  assert conditions_dict['condition4'].keys()==conditions_dict['condition5'].keys()

def get_mock_conditions_dict():
  conditions_list=read_file_contents("test/conditions.txt")
  return get_conditions_dict(conditions_list,"test","test/exclude_items.txt") 

def test_conditions_checksum_dict():
  conditions_dict = get_mock_conditions_dict()
  assert get_conditions_checksum_dict(conditions_dict,"test","checksums-after.txt") 

def test_run():
  command_line_string ="python verifyFiles.py test/conditions.txt test/fileDiff  -c checksums-after.txt -e test/exclude_items.txt"
  return_value,output = commands.getstatusoutput(command_line_string)
  assert not filecmp.cmp("test/fileDiff_differences_subject_total.txt","test/differences-ref.txt")
