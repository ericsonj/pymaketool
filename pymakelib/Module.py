# Copyright (c) 2020, Ericson Joseph
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of pyMakeTool nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import hashlib
import re
import importlib.util
import copy
from pathlib import Path
from . import preconts as K
from . import git
from abc import ABC,abstractmethod
from . import Logger

log = Logger.getLogger()

class SrcType:
    C = ['.c']
    CPP = ['.C', '.cc', '.cpp', '.CPP', '.c++', '.cp', '.cxx']
    ASM = ['.s', '.S', '.asm']


class IncType:
    C = ['.h']
    CPP = ['.h', '.hpp', '.h++', '.hh']


class StaticLibrary:
    def __init__(self, name: str, outputDir: str, rebuild=False):
        self.name = name
        self.outputDir = Path(outputDir)
        self.rebuild = rebuild

    def setRebuild(self, rebuild: bool):
        self.rebuild = rebuild

    def rebuildByCheckStr(self, checkStr: str):
        hs = hashlib.md5(checkStr.encode())
        cksumfile = Path(self.outputDir / Path('lib' + self.name + '.cksum'))
        hexstr = hs.hexdigest()
        oldHash = ""
        if cksumfile.exists():
            cksumfile = open(str(cksumfile), 'r+')
            oldHash = cksumfile.read()
        else:
            cksumfile = open(str(cksumfile), 'w')
        
        if hexstr != oldHash:
            cksumfile.seek(0)
            cksumfile.truncate(0)
            cksumfile.seek(0)
            cksumfile.write(str(hexstr))
            self.setRebuild(True)

        cksumfile.close()

class Module:
    def __init__(self, srcs, incs, flags, filename, staticLib: StaticLibrary = None):
        self.srcs = srcs
        self.incs = incs
        self.flags = flags
        self.filename = filename
        self.staticLib = staticLib
    
    def isEmpty(self):
        if not self.srcs and not self.incs and not self.staticLib:
            return True
        else:
            return False

    def getDirs(self):
        dirs = []
        for src in self.srcs:
            dirs.append(Path(str(src)).parent)
        dirs = list(set(dirs))
        return dirs

class CompilerOptions:
    def __init__(self, opts: dict):
        self.opts = opts

    def setOption(self, key, value):
        self.opts[key] = value
        return self.opts

    def addOption(self, key, value):
        if key in self.opts.keys():
            if isinstance(value, str):
                self.opts[key].append(value)
            elif isinstance(value, list):
                self.opts[key] = self.opts[key] + value
        else:
            self.opts[key] = value

class GCC_CompilerOpts(CompilerOptions):
    def __init__(self, copts):
        if isinstance(copts, CompilerOptions):
            super().__init__(copts.opts)
        elif isinstance(copts, dict):
            super().__init__(copts)
        else:
            pass

    def addGeneralOpt(self, opts:list):
        self.addOption(K.MK_KEY_GENERAL_OPTS, opts)

    def setOptimizationOpts(self, opts: list):
        self.setOption(K.MK_KEY_OPTIMIZE_OPTS, opts)

    def setControlCOpts(self, opts: list):
        self.setOption(K.MK_KEY_CONTROL_C_OPTS, opts)

    def addMacroOpts(self, macro, value=None):
        self.opts[K.MK_KEY_MACROS][macro] = value

    def getMacroValue(self, macro):
        return self.opts[K.MK_KEY_MACROS][macro]

    def setDebuggingOpts(self, opts: list):
        self.setOption(K.MK_KEY_DEBUGGING_OPTS, opts)

    def setWarningdOpts(self, opts: list):
        self.setOption(K.MK_KEY_WARNINGS_OPTS, opts)

    def isDefine(self, macro):
        if macro in self.opts[K.MK_KEY_MACROS].keys():
            return True
        else:
            return False

    def isMacroValue(self, macro, value):
        if self.isDefine(macro):
            return True if self.getMacroValue(macro) == value else False
        else:
            return False


class ModuleHandle:
    def __init__(self, modDir, gCompOpts, goal=None):
        self.modDir = modDir
        self.gCompOpts = CompilerOptions(gCompOpts)
        self.goal = goal

    def getWorkspace(self):
        wk = {
            K.MOD_WORKSPACE: self.modDir,
            K.MOD_COMPILER_OPTS: self.gCompOpts.opts
        }
        return wk

    def getAllSrcsC(self):
        return self.getAllSrcs(SrcType.C)

    def getAllSrcs(self, srcType: SrcType):
        srcs = []
        for ext in srcType:
            srcs += list(Path(self.modDir).rglob('*' + ext))
        return srcs

    def getFilesByRegex(self, regexs, relativePath=None):
        modulePath = Path(self.modDir)
        if relativePath:
            modulePath = modulePath / Path(relativePath)
        
        srcs = []
        for r in regexs:
            srcs += list(modulePath.rglob(r))

        srcs = list(dict.fromkeys(srcs))
        return srcs

    def getAllIncs(self, incType: IncType):
        incsfiles = []
        for ext in incType:
            incsfiles += list(Path(self.modDir).rglob('*' + ext))

        incs = []
        for i in incsfiles:
            incs.append(i.parent)

        incs = list(dict.fromkeys(incs))
        return incs

    def getAllIncsC(self):
        return self.getAllIncs(IncType.C)

    def getFileByNames(self, names):
        return self.getFilesByRegex(names)

    def getSrcsByPath(self, srcs):
        srcslist = []
        for src in srcs:
            srcslist.append(Path(Path(self.modDir) / src))
        return srcslist

    def getGeneralCompilerOpts(self):
        return self.gCompOpts

    def getRelaptivePath(self):
        return self.modDir

    @DeprecationWarning
    def initGitModule(self, url, folder, ispymakeproj=False, ignoreList=[]):
        absfolder = Path(Path(self.getRelaptivePath()) / Path(folder))
        
        ignoreModule = []
        ignoreModule += self.getFilesByRegex(ignoreList, relativePath=Path(folder))
        
        git.addSubmodule(url, str(absfolder), ispymakeproj, ignoreModule)

    def getGoal(self):
        return self.goal

    def __str__(self):
        return str(self.modDir) + " " + str(self.gCompOpts)

class AbstractModule(ABC):
    """Abstract class of pymaketool module

    Args:
        path (str): path to module, _mk.py file.

    Attributes:
        path (str): path of module
    """    
    def __init__(self, path) -> None:
        super().__init__()
        self.path = path

    def init(self):
        """Initialization of module
        """        
        pass

    @abstractmethod
    def getSrcs(self) -> list:
        """Abstract method to get the sources paths of module

        Returns:
            list: list of sources paths realtive to project
        """        
        pass
    
    @abstractmethod
    def getIncs(self) -> list:
        """Abstract method to get the includes paths of module

        Returns:
            list: list of includes paths realtive to project
        """        
        pass
    
    def findSrcs(self, src_type: SrcType) -> list:
        """Util method for find sources in module path

        Args:
            src_type (SrcType): Type of sources C, CPP or ASM

        Returns:
            list: list of sources paths realtive to project
        """        
        log.debug(f"find srcs in {self.path}")
        srcs = []
        for ext in src_type:
            srcs += list(Path(self.path).rglob('*' + ext))
        return srcs
        
    def findIncs(self, inc_type: IncType) -> list:
        """Util method for find includes in module path

        Args:
            inc_type (IncType): Type of includes C or CPP

        Returns:
            list: list of includes paths realtive to project
        """        
        incsfiles = []
        for ext in inc_type:
            incsfiles += list(Path(self.path).rglob('*' + ext))

        incs = []
        for i in incsfiles:
            incs.append(i.parent)

        incs = list(dict.fromkeys(incs))
        return incs

    def getAllSrcsC(self) -> list:
        """Util method for get all sources in module, type C

        Returns:
            list: list of sources paths realtive to project
        """        
        return self.findSrcs(SrcType.C)

    def getAllIncsC(self) -> list:
        """Ütil method for get all includes in module, type C 

        Returns:
            list: list of includes paths realtive to project
        """        
        return self.findIncs(IncType.C)

    def getCompilerOpts(self):
        """Get special compiler options for module
        """        
        pass


class BasicCModule(AbstractModule):
    """Basic C module, find all sources and includes in module path

    Args:
        path (str): path to module, _mk.py file.
    """
    def __init__(self, path):
        super().__init__(path)

    def getSrcs(self) -> list:
        """Return list with all sources in module path

        Returns:
            list: sources paths
        """        
        return self.getAllSrcsC()

    def getIncs(self) -> list:
        """return list with all includes in module path

        Returns:
            list: includes path 
        """        
        return self.getAllIncsC()

class ExternalModule(AbstractModule):
    """The ExternalModule object that inherits from AbstractModule for include external pymaketool module 

    Args:
        path (str): path to module, _mk.py file.

    Attributes:
        remoteModule (AbstractModule): remote module object.
    
    Raises:
            AttributeError: path is not valid
    """
    def __init__(self, path):
        super().__init__(path)
        try:
            modPath = self.getModulePath()
            if not modPath.endswith("_mk.py"):
                raise AttributeError(f"{modPath} is not a valid module path")
            lib = importlib.util.spec_from_file_location(str(modPath), str(modPath))
            mod = importlib.util.module_from_spec(lib)
            lib.loader.exec_module(mod)
            obj = getModuleInstance()[0]
            log.debug(f"create copy of module object {obj.__class__}")
            self.remoteModule = copy.deepcopy(obj)
            cleanModuleInstance()
        except Exception as ex:
            log.exception(ex)
            exit(-1)
    
    @abstractmethod
    def getModulePath(self)->str:
        """Abstract methos to get string path of external module

        Returns:
            str: path of external module
        """
        pass

    def init(self):
        """Call and return init from remote module

        Returns:
            object: may be StaticLibrary object or None
        """
        try:
            return self.remoteModule.init()
        except AttributeError as ae:
            log.debug(ae)
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def getSrcs(self):
        """Call and return getSrcs from remote module

        Returns:
            list: list of sources
        """
        return self.remoteModule.getSrcs()
        
    def getIncs(self):
        """Call and return getIncs from remote module

        Returns:
            list: list of includes
        """
        return self.remoteModule.getIncs()
    
    def getCompilerOpts(self):
        """Call and return getCompilerOpts from remote module

        Returns:
            disct: compiler options
        """
        try:
            return self.remoteModule.getCompilerOpts()
        except AttributeError as ae:
            log.debug(ae)
        except Exception as ex:
            log.exception(ex)
            exit(-1)


def ModuleClass(clazz):
    """Add class to modules of pymaketool

    Args:
        clazz (class): Class inheritance of Module.AbstractModule
    """    
    if issubclass(clazz, AbstractModule):
        log.debug(f"class \'{clazz.__name__}\' is inheritance of Module.AbstractModule")
    else:
        log.warning(f"class \'{clazz.__name__}\' in \'{__name__}\' not inheritance of Module.AbstractModule")

    classdir = str(clazz)
    log.debug(f"class dir {classdir}")
    m = re.search(r"<class \'(?P<dir>[a-zA-Z\./_-]+)\'>", classdir)
    modulePath = None
    if m:
        p = Path(m.group('dir'))
        modulePath = p.parent

    obj = clazz(modulePath)
    global ModulesInstances
    try:
        _ = ModulesInstances
    except NameError:
        log.debug(f"create global modules list")
        ModulesInstances = []

    
    log.debug(f"add new instance of ModuleClass \'{clazz.__name__}\' with path {modulePath}")
    ModulesInstances.append(obj)


def getModuleInstance() -> AbstractModule:
    try:
        _ = ModulesInstances
        return ModulesInstances
    except NameError:
        log.debug("not ModuleClass in project")
        pass
    return None


def cleanModuleInstance():
    try:
        global ModulesInstances
        log.debug(f"clean global modules list")
        ModulesInstances = []
    except Exception as ex:
        log.exception(ex)
        log.debug("not ModulesInstances in project")
        pass