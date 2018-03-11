import pytest
import commands

def test_run():
    command_line_string = "python plot_superimpose_matrix.py test/test_differences_plot.txt test/test_predict_plot.txt test/test_superimpose_plot.pdf"
    return_value, output = commands.getstatusoutput(command_line_string)
    print (return_value)
    assert not return_value, output

