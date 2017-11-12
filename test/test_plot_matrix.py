import pytest
import commands

def test_run():
  command_line_string = "python plot_matrix.py test/test_differences_plot.txt test/test_differences_plot.pdf"
  return_value, output = commands.getstatusoutput(command_line_string)
  assert not return_value, output
