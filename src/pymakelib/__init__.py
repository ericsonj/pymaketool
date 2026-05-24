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

import os
import inspect
from abc import ABC,abstractmethod
import logging
from logging import Logger as SysLogger, PlaceHolder
from typing import Dict, List, Optional, TypedDict, Union
from dataclasses import dataclass, field

class _PhonyTargetRequired(TypedDict):
    script: Union[str, List[str]]

class PhonyTarget(_PhonyTargetRequired, total=False):
    deps: Union[str, List[str]]
    logkey: str


# ---------------------------------------------------------------------------
# Typed configuration containers (new API)
# ---------------------------------------------------------------------------

@dataclass
class CompilerOpts:
    """Type-safe compiler options — replaces the magic-string dict from getCompilerOpts().

    Pass an instance (or return it from ProjectConfig.compiler_opts()) instead of
    a raw dict.  All keys map to the existing MK_KEY_* constants in preconts.py.

    Attributes:
        macros:       preprocessor macros, e.g. {'DEBUG': None, 'VER': '2'}
        machine:      machine/arch flags, e.g. ['-mthumb', '-mcpu=cortex-m4']
        optimize:     optimisation flags, e.g. ['-O2']
        debugging:    debug-info flags, e.g. ['-g3']
        preprocessor: preprocessor flags, e.g. ['-MP', '-MMD']
        warnings:     warning flags, e.g. ['-Wall', '-Werror']
        standard:     language-standard flags, e.g. ['-std=c99']
        general:      any other flags not covered above
    """
    macros:       Dict[str, object] = field(default_factory=dict)
    machine:      List[str]         = field(default_factory=list)
    optimize:     List[str]         = field(default_factory=list)
    debugging:    List[str]         = field(default_factory=list)
    preprocessor: List[str]         = field(default_factory=list)
    warnings:     List[str]         = field(default_factory=list)
    standard:     List[str]         = field(default_factory=list)
    general:      List[str]         = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to the legacy dict format consumed by prelib/generator."""
        from . import preconts as K
        return {
            K.MK_KEY_MACROS:            self.macros,
            K.MK_KEY_MACHINE_OPTS:      self.machine,
            K.MK_KEY_OPTIMIZE_OPTS:     self.optimize,
            K.MK_KEY_DEBUGGING_OPTS:    self.debugging,
            K.MK_KEY_PREPROCESSOR_OPTS: self.preprocessor,
            K.MK_KEY_WARNINGS_OPTS:     self.warnings,
            K.MK_KEY_CONTROL_C_OPTS:    self.standard,
            K.MK_KEY_GENERAL_OPTS:      self.general,
        }

    def define_flag(self, name: str) -> 'CompilerOpts':
        """Bare define — expands to -DNAME with no value."""
        self.macros[name] = None
        return self

    def define_string(self, name: str, value: str) -> 'CompilerOpts':
        """Quoted string define — expands to -DNAME=\"value\"."""
        self.macros[name] = value
        return self

    def define_raw(self, name: str, value: str) -> 'CompilerOpts':
        """Raw (unquoted) define — expands to -DNAME=value. Use for filenames or C expressions."""
        self.macros[name] = Define(value)
        return self

    def define_int(self, name: str, value: int) -> 'CompilerOpts':
        """Integer define — expands to -DNAME=42."""
        self.macros[name] = value
        return self


@dataclass
class LinkerOpts:
    """Type-safe linker options — replaces the magic-string dict from getLinkerOpts().

    Attributes:
        script:  linker-script flags, e.g. ['-T', 'link.ld']
        machine: machine flags for the linker, e.g. ['-mthumb']
        general: general linker flags, e.g. ['--gc-sections']
        opts:    raw linker option flags
        libs:    library link flags, e.g. ['-lm', '-lc']
    """
    script:  List[str] = field(default_factory=list)
    machine: List[str] = field(default_factory=list)
    general: List[str] = field(default_factory=list)
    opts:    List[str] = field(default_factory=list)
    libs:    List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'LINKER-SCRIPT': self.script,
            'MACHINE-OPTS':  self.machine,
            'GENERAL-OPTS':  self.general,
            'LINKER-OPTS':   self.opts,
            'LIBRARIES':     self.libs,
        }


@dataclass
class ProjectSettings:
    """Type-safe project settings — replaces the dict from getProjectSettings().

    Attributes:
        name:       project name written to PROJECT in vars.mk
        output_dir: directory for compiled objects, e.g. 'build/obj/'
    """
    name:       str
    output_dir: str = 'build/obj/'

    def to_dict(self) -> dict:
        from . import preconts as K
        return {
            K.PROJSETT_PROJECTNAME: self.name,
            K.PROJSETT_FOLDEROUT:   self.output_dir,
        }


@dataclass
class CompilerSet:
    """Toolchain paths — replaces the 17-key dict from getCompilerSet().

    Prefer factory functions over hand-filling this:
        from pymakelib.toolchain import get_gcc_linux, get_gcc_arm_none_eabi
        compiler_set = get_gcc_linux()
        compiler_set = get_gcc_arm_none_eabi('/opt/arm/bin/')

    All field names match the COMPILERSET_* keys in preconts.py.
    """
    CC:        str = 'gcc'
    CXX:       str = 'g++'
    LD:        str = 'gcc'
    AR:        str = 'ar'
    AS:        str = 'as'
    OBJCOPY:   str = 'objcopy'
    SIZE:      str = 'size'
    OBJDUMP:   str = 'objdump'
    NM:        str = 'nm'
    RANLIB:    str = 'ranlib'
    STRINGS:   str = 'strings'
    STRIP:     str = 'strip'
    CXXFILT:   str = 'c++filt'
    ADDR2LINE: str = 'addr2line'
    READELF:   str = 'readelf'
    ELFEDIT:   str = 'elfedit'
    INCLUDES:  List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {k: v for k, v in vars(self).items()}
        return d


@dataclass
class Target:
    """A single build target entry for getTargetsScript() / ProjectConfig.targets().

    Attributes:
        file:   output file path (the thing being built), e.g. 'build/myapp.elf'
        script: shell command tokens — joined with spaces into one Makefile recipe line.
                Use MKVARS constants and && for chaining:
                    ['@mkdir -p $(dir $@) &&', MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS]
        logkey: short label shown in build output (auto-padded for alignment).

    Target dict ORDER is the build chain — each target depends on the previous one.
    The special key 'TARGET' always receives $(OBJECTS) $(SLIBS_OBJECTS) as deps.
    """
    file:   str
    script: List[str]
    logkey: str = '>>'

    def to_dict(self) -> dict:
        return {
            'FILE':   self.file,
            'SCRIPT': self.script if isinstance(self.script, list) else [self.script],
            'LOGKEY': self.logkey,
        }


__all__ = [
    # Project-level configuration (Makefile.py)
    "AbstractMake",
    "Makeclass",
    "ProjectConfig",
    # Typed configuration containers (new API)
    "CompilerOpts",
    "LinkerOpts",
    "ProjectSettings",
    "CompilerSet",
    "Target",
    # Compiler-options helpers
    "MKVARS",
    "Define",
    "MOD_PATH",
    # Phony target type
    "PhonyTarget",
    # .env helpers
    "load_dotenv",
    "resolve_env",
    # Module system — module authors import this sub-module
    "module",
    # Programmatic API
    "Pymaketool",
]

FORMATTER = logging.Formatter("%(levelname)-8s%(filename)s:%(lineno)d  %(message)s")

class Logger:
    __instance = None
    @staticmethod
    def getInstance():
        """ Static access method. """
        if Logger.__instance == None:
            Logger()
        return Logger.__instance

    @staticmethod
    def getLogger() -> logging.Logger:
        return Logger.getInstance().log

    def __init__(self):
        """ Virtually private constructor. """
        if Logger.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Logger.__instance = self
        self.log = SysLogger.manager.getLogger('pymaketool')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(FORMATTER)
        self.log.addHandler(console_handler)
        self.log.setLevel(os.environ.get('LOGLEVEL', 'NOTSET'))

__log = Logger().getLogger()

class MKVARS():
    LD      = "$(LD)"
    OBJECTS = '$(OBJECTS)' 
    LDFLAGS = '$(LDFLAGS)'
    OBJCOPY = '$(OBJCOPY)'
    NM          = '$(NM)'
    RANLIB      = '$(RANLIB)'
    STRINGS     = '$(STRINGS)'
    STRIP       = '$(STRIP)'
    CXXFILT     = '$(CXXFILT)'
    ADDR2LINE   = '$(ADD2LINE)'
    READELF     = '$(READELF)'
    CELFEDIT    = '$(ELFEDIT)'
    SIZE    = '$(SIZE)'
    TARGET  = '$(TARGET)'
    PROJECT = '$(PROJECT)'
    STATIC_LIBS = '$(SLIBS_NAMES)'

def MOD_PATH(wk):
    return wk['modPath']


class Define:
    """
    Direct define: { '__USE_FILE__': D('file.h') } => -D__USE_FILE__=file.h
    """
    def __init__(self, value):
        self.value = value
    def getDefine(self):
        if isinstance(self.value, str):
            return self.value
        else:
            return ''
    def __str__(self):
        return str(self.getDefine())
    def __repr__(self):
        return str(self.getDefine())


class AbstractMake(ABC):
    @abstractmethod
    def getProjectSettings(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def getTargetsScript(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def getCompilerSet(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def getCompilerOpts(self, **kwargs) -> dict:
        pass

    @abstractmethod
    def getLinkerOpts(self, **kwargs) -> dict:
        pass

    def getPhonyTargets(self) -> dict[str, PhonyTarget]:
        return {}
    
    def getIgnoreConfig(self) -> dict:
        """Return ignore configuration for module discovery.
        
        Override to customize ignore behavior. Returns dict with keys:
        - 'use_gitignore': bool (default True) - whether to read .gitignore
        - 'ignore_list': List[str] (default []) - additional patterns to ignore
        
        Example:
            def getIgnoreConfig(self):
                return {
                    'use_gitignore': True,
                    'ignore_list': ['tests/', 'vendor/']
                }
        """
        return {}


class ProjectConfig(AbstractMake):
    """Ready-to-subclass base for Makefile.py — replaces AbstractMake for new projects.

    Override only the attributes/methods you need.  All compiler options are
    typed so your IDE can autocomplete field names.

    Minimal usage:
        from pymakelib import ProjectConfig, Makeclass, MKVARS, Target
        from pymakelib.toolchain import get_gcc_linux

        @Makeclass
        class Build(ProjectConfig):
            name         = 'myapp'
            compiler_set = get_gcc_linux()

            def compiler_opts(self, opts: CompilerOpts) -> CompilerOpts:
                opts.optimize     = ['-O2']
                opts.debugging    = ['-g3']
                opts.warnings     = ['-Wall']
                opts.standard     = ['-std=c99']
                opts.preprocessor = ['-MP', '-MMD']
                return opts

            def targets(self):
                return {'TARGET': Target(
                    file   = f'build/{self.name}',
                    script = [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS],
                    logkey = 'OUT',
                )}

    Attributes:
        name:         project name (defaults to current directory name)
        output_dir:   object output directory (default 'build/obj/')
        compiler_set: toolchain — set to get_gcc_linux() etc. (REQUIRED)
        addons:       list of addon classes, e.g. [EclipseAddon, VSCodeAddon]
        env_file:     optional path to a .env file loaded before build config
        use_gitignore: whether to read .gitignore for module discovery (default True)
        ignore_list:  additional patterns to ignore during module discovery (default [])
    """
    name:          str              = ''
    output_dir:    str              = 'build/obj/'
    compiler_set:  Optional[object] = None
    addons:        List[type]       = field(default_factory=list) if False else []
    env_file:      Optional[str]    = None
    use_gitignore: bool             = True
    ignore_list:   List[str]        = field(default_factory=list) if False else []

    def getProjectSettings(self, **kwargs) -> dict:
        n = self.name or os.path.basename(os.getcwd())
        return ProjectSettings(name=n, output_dir=self.output_dir).to_dict()

    def getCompilerSet(self, **kwargs) -> dict:
        if self.compiler_set is None:
            raise NotImplementedError(
                f"{self.__class__.__name__}: set 'compiler_set = get_gcc_linux()' "
                "(or another preset) before using ProjectConfig."
            )
        cs = self.compiler_set
        return cs.to_dict() if isinstance(cs, CompilerSet) else cs

    def getCompilerOpts(self, **kwargs) -> dict:
        opts = CompilerOpts()
        fn = getattr(self.__class__, 'compiler_opts', None)
        if fn is not None and callable(fn):
            opts = fn(self, opts)
        return opts.to_dict() if isinstance(opts, CompilerOpts) else opts

    def getLinkerOpts(self, **kwargs) -> dict:
        opts = LinkerOpts()
        fn = getattr(self.__class__, 'linker_opts', None)
        if fn is not None and callable(fn):
            opts = fn(self, opts)
        return opts.to_dict() if isinstance(opts, LinkerOpts) else opts

    def getTargetsScript(self, **kwargs) -> dict:
        fn = getattr(self.__class__, 'targets', None)
        if fn is None or not callable(fn):
            raise NotImplementedError(
                f"{self.__class__.__name__}: define a targets() method returning "
                "a dict of target-name → Target(...)."
            )
        result = fn(self)
        if isinstance(result, dict) and result:
            first_val = next(iter(result.values()))
            if isinstance(first_val, Target):
                return {name: t.to_dict() for name, t in result.items()}
        return result
    
    def getIgnoreConfig(self) -> dict:
        """Return ignore configuration from attributes or override method."""
        return {
            'use_gitignore': self.use_gitignore,
            'ignore_list': self.ignore_list,
        }


def Makeclass(clazz):
    obj = clazz()
    if not isinstance(obj, AbstractMake):
        __log.warning(f"class \'{clazz.__name__}\' in Makefile.py not inheritance of pymakelib.AbstractMake")
    # Auto-load .env if declared
    env_file = getattr(obj, 'env_file', None)
    if env_file:
        try:
            from .env import load_dotenv as _load_dotenv
            _load_dotenv(env_file)
        except Exception as _e:
            __log.warning(f"[pymaketool] Could not load env_file '{env_file}': {_e}")
    # Register addons declared on ProjectConfig subclasses
    addons_list = getattr(obj, 'addons', None)
    if addons_list:
        try:
            from . import addon as _addon_mod
            for _addon_cls in addons_list:
                _addon_mod.add(_addon_cls)
        except Exception as _e:
            __log.warning(f"[pymaketool] Could not register addon: {_e}")
    global ProjectInstance
    ProjectInstance = obj


def getProjectInstance() -> AbstractMake:
    try:
        _ = ProjectInstance
        return ProjectInstance
    except NameError:
        __log.debug("not Makeclass mode")
        pass
    return None

## More OOP for pymaketool

from pathlib import Path
import copy
from . import prelib as plib
from . import module
from .env import load_dotenv, resolve_env
import sys

class Pymaketool():

    def __init__(self, workpath='./'):
        self.workpath = workpath
        sys.path.append(str(self.workpath))
        self.projSettings, self.compilerOpts, self.compilerSettings = plib.read_Makefilepy(self.workpath)


    def getModulesPaths(self) -> list:
        return sorted(
            set(Path(self.workpath).rglob('*[.|_]mk.py')) | set(Path(self.workpath).rglob('mk.py'))
        )


    def readModules(self, modulesPaths) -> list:
        self.modules = []
        for filename in modulesPaths:
            mod = plib.readModule(filename, copy.deepcopy(self.compilerOpts), None, project_root=Path(self.workpath).resolve())
            self.modules.extend(mod)
        return self.modules
    
    def read_modules(self, modulesPaths) -> List[module.AbstractModule]:
        self.modules = []
        for filename in modulesPaths:
            mod = plib.read_module(filename, copy.deepcopy(self.compilerOpts), None, project_root=Path(self.workpath).resolve())
            self.modules.extend(mod)
        return self.modules