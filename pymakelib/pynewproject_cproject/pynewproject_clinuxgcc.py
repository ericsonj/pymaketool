import datetime
import os
from pathlib import Path
from pymakelib import nproject
from pkg_resources import resource_filename
import argparse

class CLinuxGCC(nproject.BasicGenerator):
    """Generate basic C linux gcc project 
    """
    def info(self):
        return {
            "name": "C Project",
            "desc": "C Linux GCC Project"
        }

    def get_temp_files(self):
        return [
            'app/inc/main.h',
            'app/src/main.c',
            'app/app_mk.py',
            'makefile.mk',
            'Makefile',
            'Makefile.py',
            ".project",
            ".pymakeproj/.cproject_template",
            ".pymakeproj/.language.settings_template",
            ".settings",
        ]

    def get_attrs(self, **kwargs) -> dict:

        args = kwargs['args']
        print(args)
        args_dict = {}
        for a in args:
            key = a.split('=')[0]
            value = a.split('=')[1]
            args_dict[key] = value
        args = args_dict

        tokens = {
            'author':       'Ericson Joseph',
            'date':         datetime.datetime.now().strftime("%b %d %Y"),
            'project_name': 'c_temp'
        }
        tokens['author']       = input("(author) Your name: ") if not 'author' in args else args['author']
        tokens['project_name'] = input("(project_name) Your project name: ") if not 'project_name' in args else args['project_name']

        output_dir = Path( Path(os.getcwd()) / Path(tokens['project_name'])) 

        gzip_file = resource_filename("pymakelib.resources.templates", "clinuxgcc.tar.gz")

        return {
            "temp_name":        "clinuxgcc",
            "temp_gzip_file":   gzip_file,
            "temp_files":       self.get_temp_files(),
            "temp_tokens":      tokens,
            "output_folder":    output_dir,
        }
