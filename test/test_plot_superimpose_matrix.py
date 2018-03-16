import pytest
import commands

def test_run():
    command_line_string = "python plot_superimpose_matrix.py test/predict_test/test_differences.txt test/predict_test/triangular-S_0.6_test_data_matrix.txt test/test_superimpose_plot.png"
    return_value, output = commands.getstatusoutput(command_line_string)
    print (return_value)
    assert not return_value, output

