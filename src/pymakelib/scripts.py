#!/usr/bin/env python3
"""
Script entry points for pymaketool
"""

import os
import sys
from pathlib import Path

def get_script_path(script_name):
    """Get the path to a script file"""
    # Scripts are now inside the pymakelib package
    pkg_dir = Path(__file__).parent
    script_path = pkg_dir / "scripts" / script_name
    return str(script_path)

def run_script(script_name):
    """Run a script with the current Python interpreter"""
    script_path = get_script_path(script_name)
    if os.path.exists(script_path):
        # Execute the script with the current Python interpreter
        os.execv(sys.executable, [sys.executable, script_path] + sys.argv[1:])
    else:
        print(f"Error: Script {script_path} not found")
        sys.exit(1)

def run_pymaketool():
    """Entry point for pymaketool script"""
    run_script("pymaketool")

def run_pymaketesting():
    """Entry point for pymaketesting script"""
    run_script("pymaketesting")

def run_pybuildanalyzer():
    """Entry point for pybuildanalyzer script"""
    run_script("pybuildanalyzer")

def run_pybuildanalyzer2():
    """Entry point for pybuildanalyzer2 script"""
    run_script("pybuildanalyzer2")

def run_pymakedot():
    """Entry point for pymakedot script"""
    run_script("pymakedot")

def run_pynewproject():
    """Entry point for pynewproject script"""
    run_script("pynewproject")
