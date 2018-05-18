import pytest
import commands

def test_run():
    command_line_string = "python plot_matrix.py test/predict_test/test_differences.txt -t test/predict_test/triangular-S_0.6_test_data_matrix.txt test_plot_matrix.png"
    return_value, output = commands.getstatusoutput(command_line_string)
    print (return_value)
    assert not return_value, output

