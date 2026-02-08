# pymaketool
<p align=center>
<img src="https://img.shields.io/pypi/l/pymaketool.svg">
<img src="https://img.shields.io/pypi/wheel/pymaketool.svg">
<img src="https://img.shields.io/badge/python-%3E=_3.6-green.svg">
<img src="https://img.shields.io/github/v/tag/ericsonj/pymaketool">
<img src="https://github.com/ericsonj/pymaketool/workflows/Test/badge.svg?branch=master">
</p>

**pymaketool** is an elegant and simple tool to build and manage large C/C++ projects and libraries.
The main purpose is to simplify the build process by using Python to find and organize source files.

<img src="https://github.com/ericsonj/pymaketool/raw/master/images/makefile_pyfile.jpg" alt="" title="makefile vs pymaketool" width="500" />

## Quick Start

Install required packages:

### Ubuntu
```bash
$ sudo apt-get install -y gcc make python3 python3-pip python3-gi python3-gi-cairo gir1.2-gtk-3.0 git time zip
```

### Fedora
```bash
$ sudo dnf install python3 python3-pip python3-gobject gtk3 time zip git gcc
```

### Arch Linux
```bash
$ sudo pacman -S gcc make python python-pip python-gobject gtk3 time zip git 
```

Install pymaketool:
```bash
$ pip3 install pymaketool 
```

## Quick Start with Poetry

If you prefer using [Poetry](https://python-poetry.org/) for dependency management, you can set up your C project as a Poetry project:

### Install Poetry
```bash
$ curl -sSL https://install.python-poetry.org | python3 -
```

### Create a new C project with Poetry
```bash
$ pynewproject CLinuxGCC
  (author) Your name: Ericson
  (project_name) Your project name: hello

$ cd hello

# Initialize Poetry in your project
hello$ poetry init --name hello --dependency pymaketool

# Install dependencies
hello$ poetry install
```

### Build using Poetry
```bash
# Clean the project
hello$ poetry run make clean

# Build the project
hello$ poetry run make

# Run the executable
hello$ ./Release/hello
```

### Example pyproject.toml for a C project
```toml
[project]
name = "hello"
version = "0.1.0"
description = "My C project using pymaketool"
authors = [{ name = "Your Name", email = "your@email.com" }]
requires-python = ">=3.10"
dependencies = ["pymaketool"]

[build-system]
requires = ["poetry-core>=2.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.poetry.scripts]
build = "subprocess:run"
```

Using Poetry ensures consistent Python environments across different machines and simplifies dependency management for your build tools.

Create new basic C project.
```bash
$ pynewproject CLinuxGCC
  (author) Your name: Ericson
  (project_name) Your project name: hello

$ cd hello

hello$ make clean

hello$ make

hello$ ./Release/hello
```
Note: This example uses **EclipseAddon** by default; pymaketool generates the files *.settings/language.settings.xml* and *.cproject*.

## Quick start in Docker

Pull the image and run a container:
```bash
$ docker pull ericsonjoseph/pymaketool

$ docker run -it ericsonjoseph/pymaketool

ubuntu@$ pynewproject CLinuxGCC
```

## Quick Info

**pymaketool** processes code modules as objects. These objects are defined by files ending with **_mk.py**. With Python, you can write code to discover and retrieve source files and include paths, e.g.:

```python
# File app_mk.py

from pymakelib import module

@module.ModuleClass
class App(module.AbstractModule):

    def getSrcs(self):
        # Get all .c source files in the current folder ./app/
        # Returns e.g.: [ 'app/app.c' ]
        return self.getAllSrcsC() 

    def getIncs(self):
        # Get all include paths in the current folder ./app/
        # Returns e.g.: [ 'app' ]
        return self.getAllIncsC()

```

The file app_mk.py can be shorter and simpler, e.g.:

```python
# File app_mk.py

from pymakelib import module

# BasicCModule inherits from AbstractModule and implements getSrcs and getIncs.
@module.ModuleClass
class App(module.BasicCModule):
    pass
```

The file app_mk.py in raw style:

```python
# File app_mk.py

from pymakelib import module

@module.ModuleClass
class App():
    
    def getSrcs(self):
        return [
            'app/app.c'
        ]

    def getIncs(self):
        return [
            'app'
        ]
    
```

Remote modules can be loaded as static libraries with custom compiler flags, e.g.:

```python
# File extlib_mk.py

from pymakelib import module

@module.ModuleClass
class ExtLib(module.ExternalModule):
    
    def init(self):
        # Compile modulelib as a static library (Optional)
        return module.StaticLibrary("modulelib", "Release", rebuild=True)
     
    def getModulePath(self)->str:
        # Location of module
        return '/LIBS/module_lib/module_lib_mk.py'


    def getCompilerOpts(self):
        # Override method and set special compiler flags (Optional)
        opts = project.getCompilerOpts()
        opts['CONTROL-C-OPTS'] = ['-std=c99']
        return opts
    
```

For install guide go to [install-guide](docs/install/install-guide.md)

For more documentation go to [Read the Docs](https://pymaketool.readthedocs.io/en/latest/) 