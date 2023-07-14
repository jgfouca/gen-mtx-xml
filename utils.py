"""
Utilities
"""

import os, sys, re, signal, subprocess, site, time
from importlib import import_module
from pathlib import Path

###############################################################################
def expect(condition, error_msg, exc_type=SystemExit, error_prefix="ERROR:"):
###############################################################################
    """
    Similar to assert except doesn't generate an ugly stacktrace. Useful for
    checking user error, not programming error.

    >>> expect(True, "error1")
    >>> expect(False, "error2")
    Traceback (most recent call last):
        ...
    SystemExit: ERROR: error2
    """
    if not condition:
        msg = error_prefix + " " + error_msg
        raise exc_type(msg)

###############################################################################
def run_cmd(cmd, input_str=None, from_dir=None, verbose=None, dry_run=False,
            arg_stdout=subprocess.PIPE, arg_stderr=subprocess.PIPE, env=None, combine_output=False):
###############################################################################
    """
    Wrapper around subprocess to make it much more convenient to run shell commands

    >>> run_cmd('ls file_i_hope_doesnt_exist')[0] != 0
    True
    """
    arg_stderr = subprocess.STDOUT if combine_output else arg_stderr
    from_dir = str(from_dir) if from_dir else from_dir

    if verbose:
        print("RUN: {}\nFROM: {}".format(cmd, os.getcwd() if from_dir is None else from_dir))

    if dry_run:
        return 0, "", ""

    if input_str is not None:
        stdin = subprocess.PIPE
        input_str = input_str.encode('utf-8')
    else:
        stdin = None

    proc = subprocess.Popen(cmd,
                            shell=True,
                            stdout=arg_stdout,
                            stderr=arg_stderr,
                            stdin=stdin,
                            cwd=from_dir,
                            env=env)

    output, errput = proc.communicate(input_str)
    if output is not None:
        try:
            output = output.decode('utf-8', errors='ignore')
            output = output.strip()
        except AttributeError:
            pass
    if errput is not None:
        try:
            errput = errput.decode('utf-8', errors='ignore')
            errput = errput.strip()
        except AttributeError:
            pass

    stat = proc.wait()

    return stat, output, errput

###############################################################################
def run_cmd_no_fail(cmd, input_str=None, from_dir=None, verbose=None, dry_run=False,
                    arg_stdout=subprocess.PIPE, arg_stderr=subprocess.PIPE, env=None, combine_output=False, exc_type=SystemExit):
###############################################################################
    """
    Wrapper around subprocess to make it much more convenient to run shell commands.
    Expects command to work. Just returns output string.

    >>> run_cmd_no_fail('echo foo') == 'foo'
    True
    >>> run_cmd_no_fail('echo THE ERROR >&2; false') # doctest:+ELLIPSIS
    Traceback (most recent call last):
        ...
    SystemExit: ERROR: Command: 'echo THE ERROR >&2; false' failed with error ...

    >>> run_cmd_no_fail('grep foo', input_str='foo') == 'foo'
    True
    >>> run_cmd_no_fail('echo THE ERROR >&2', combine_output=True) == 'THE ERROR'
    True
    """
    stat, output, errput = run_cmd(cmd, input_str=input_str, from_dir=from_dir, verbose=verbose, dry_run=dry_run,
                                   arg_stdout=arg_stdout, arg_stderr=arg_stderr, env=env, combine_output=combine_output)
    if stat != 0:
        # If command produced no errput, put output in the exception since we
        # have nothing else to go on.
        errput = output if not errput else errput
        if errput is None:
            errput = ""

        expect(False, "Command: '{}' failed with error '{}' from dir '{}'".format(cmd, errput, os.getcwd() if from_dir is None else from_dir), exc_type=exc_type)

    return output

###############################################################################
def check_minimum_python_version(major, minor):
###############################################################################
    """
    Check your python version.

    >>> check_minimum_python_version(sys.version_info[0], sys.version_info[1])
    >>>
    """
    msg = "Python " + str(major) + ", minor version " + str(minor) + " is required, you have " + str(sys.version_info[0]) + "." + str(sys.version_info[1])
    expect(sys.version_info[0] > major or
           (sys.version_info[0] == major and sys.version_info[1] >= minor), msg)
