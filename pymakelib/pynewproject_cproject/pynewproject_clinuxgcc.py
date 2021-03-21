import datetime
import os
from pathlib import Path
from pymakelib import nproject
from pkg_resources import resource_filename

class CLinuxGCC(nproject.BasicGenerator):
    """Generate basic C linux gcc project 
    """
    def info(self):
        return {
            "name": "C Project",
            "desc": "C Linux GCC Project"
        }

    def temp_files(self):
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

    def get_attrs(self) -> dict:

        temp_tokens = {
            'author':       'Ericson Joseph',
            'date':         datetime.datetime.now().strftime("%b %d %Y"),
            'project_name': 'c_temp'
        }
        temp_tokens['author']       = input("Your name: ")
        temp_tokens['project_name'] = input("Your project name: ")

        output_dir = Path( Path(os.getcwd()) / Path(temp_tokens['project_name'])) 

        gzip_file = resource_filename("pymakelib.resources.templates", "clinuxgcc.tar.gz")

        return {
            "temp_name":        "clinuxgcc",
            "temp_gzip_file":   gzip_file,
            "temp_files":       self.temp_files(),
            "temp_tokens":      temp_tokens,
            "output_folder":    output_dir,
        }
