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
from pathlib import Path
from . import preconts as K
from . import git
from abc import ABC,abstractmethod
from . import Log

log = Log.getLogger()

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
    
    # def init(self, mh: ModuleHandle):
    #     pass

    @abstractmethod
    def getSrcs(self, mh: ModuleHandle) -> list:
        pass
    
    @abstractmethod
    def getIncs(self, mh: ModuleHandle) -> list:
        pass

    # def getCompilerOpts(self, mh: ModuleHandle):
    #     return mh.getGeneralCompilerOpts()
    

def ModuleClass(clazz):
    obj = clazz()
    if not isinstance(obj, AbstractModule):
        log.warning(f"class \'{clazz.__name__}\' in \'{__name__}\' not inheritance of Module.AbstractModule")
    
    global ModulesInstances
    try:
        _ = ModulesInstances
    except NameError:
        log.debug(f"create global modules list")
        ModulesInstances = []

    log.debug(f"add new instance of ModuleClass \'{clazz.__name__}\'")
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
        log.debug(f"clean instances of \'{type(ModulesInstances).__name__}\'")
        ModulesInstances = []
    except Exception as ex:
        log.exception(ex)
        log.debug("not ModulesInstances in project")
        pass