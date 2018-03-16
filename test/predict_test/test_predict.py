import pytest
import commands
import random
import sys

#shuffled_subject = [1,4,2,0,3]
def test_run():
      command_line_string = "python predict.py test/predict_test/test_differences.txt 0.6 triangular-S -s 3"
      return_value, output = commands.getstatusoutput(command_line_string)
      assert not return_value, output
