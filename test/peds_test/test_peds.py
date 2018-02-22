import pytest
import commands

def test_peds():
    command_line = "python peds.py -db test/peds_test/tracePFS.sqlite3 -ofile test/peds_test/diff_file_centos6-7.txt"
    return_value, output = commands.getstatusoutput(command_line)
    assert not return_value, output


