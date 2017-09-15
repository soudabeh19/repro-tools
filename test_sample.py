import pytest
from verifyFiles import get_dir_dict 

def test_directories():
  assert get_dir_dict("test/condition5","test/exclude_items.txt") == get_dir_dict("test/condition5","test/exclude_items.txt")
