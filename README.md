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

<img src="images/makefile_pyfile.jpg" alt="Kitten" title="makefile vs pymaketool" width="500" />

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

For more documentation go to [Read the Docs](https://pymaketool.readthedocs.io/en/latest/) 