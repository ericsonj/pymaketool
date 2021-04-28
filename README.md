# pymaketool
<p align=center>
<img src="https://img.shields.io/pypi/l/pymaketool.svg">
<img src="https://img.shields.io/pypi/wheel/pymaketool.svg">
<img src="https://img.shields.io/badge/python-%3E=_3.6-green.svg">
<img src="https://img.shields.io/github/v/tag/ericsonj/pymaketool">
<img src="https://github.com/ericsonj/pymaketool/workflows/Test/badge.svg?branch=master">
</p>

**pymaketool** is an elegant and simple tool to build and manager large C/C++ projects and libraries.
The main purpose is to ease the build process of a project using Python for find and organize file sources.

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
Note: this example use **EclipseAddon** by default, pymaketool generate files *.setting/language.settings.xml* and *.cproject*.

## Quick start in Docker

Pull imagen and run container:
```bash
$ docker pull ericsonjoseph/pymaketool

$ docker run -it ericsonjoseph/pymaketool

ubuntu@$ pynewproject CLinuxGCC
```

## Quick Info

 **pymaketool** process modules of code like objects. These objects ware define by files **_mk.py*. With Python you can code how to discover and get source files and include paths, e.g.:

```python
# File app_mk.py

from pymakelib import module

@module.ModuleClass
class App(module.AbstractModule):

    def getSrcs(self):
        # Get all sources .c in current folder ./app/
        # return [ 'app/app.c' ]
        return self.getAllSrcsC() 

    def getIncs(self):
        # Get all include paths in current folder ./app/
        # return [ 'app/app.c' ]
        return self.getAllIncsC()

```

The file app_mk.py could be more short and ease, e.g.:

```python
# File app_mk.py

from pymakelib import module

# BasicCModule inherits from AbstractModule and implement getSrcs and getIncs.
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

Remote modules could be load like static libraries  and with special compiler flags. e.g:

```python
# File extlib_mk.py

from pymakelib import module

@module.ModuleClass
class ExtLib(module.ExternalModule):
    
    def init(self):
        # Compile modulelib like static library (Optional)
        return module.StaticLibrary("modulelib", "Release", rebuild=True)
     
    def getModulePath(self)->str:
        # Location of module
        return '/LIBS/module_lib/module_lib_mk.py'


    def getCompilerOpts(self):
        # Override method and set speacial compiler flags (Optional)
        opts = project.getCompilerOpts()
        opts['CONTROL-C-OPTS'] = ['-std=c99']
        return opts
    
```

For install guide go to [install-guide](docs/install/install-guide.md)

For more documentation go to [Read the Docs](https://pymaketool.readthedocs.io/en/latest/) 