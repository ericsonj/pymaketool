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
import sys
import warnings
from pathlib import Path
from typing import Final, List, Optional
from . import preconts as K
from . import git
from abc import ABC, abstractmethod, ABCMeta
from . import Logger

log = Logger.getLogger()


class SrcType:
    C: Final[List[str]] = [".c"]
    CPP: Final[List[str]] = [".C", ".cc", ".cpp", ".CPP", ".c++", ".cp", ".cxx"]
    ASM: Final[List[str]] = [".s", ".S", ".asm"]
    C_AND_ASM: Final[List[str]] = C + ASM
    CPP_AND_ASM: Final[List[str]] = CPP + ASM


class IncType:
    C: Final[List[str]] = [".h"]
    CPP: Final[List[str]] = [".h", ".hpp", ".h++", ".hh"]


class StaticLibrary:
    def __init__(
        self, name: str, outputDir: str, rebuild=False, lib_linked_opts=None, orden=1
    ):
        self.name = name
        self.orden = orden
        self.outputDir = Path(outputDir)
        self.rebuild = rebuild
        self.mkkey = self.name.upper()
        self.lib_name = "lib" + self.name + ".a"
        self.library = self.outputDir / Path(self.lib_name)
        self.lib_objs = f"{self.mkkey}_OBJECTS = $({self.mkkey}_CSRC:%.c=$({self.mkkey}_OUTPUT)/%.o) $({self.mkkey}_CSRC:%.s=$({self.mkkey}_OUTPUT)/%.o)"
        self.lib_objs_compile = f'$({self.mkkey}_OUTPUT)/%.o: %.c\n\t$(call logger-compile-lib,"CC","{self.library}",$<)\n\t@mkdir -p $(dir $@)\n\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<'
        self.lib_compile = f'$({self.mkkey}_AR): $({self.mkkey}_OBJECTS)\n\t$(call logger-compile,"AR",$@)\n\t$(AR) -rc $@ $(filter %.o,$({self.mkkey}_OBJECTS))'
        self.lib_linked_opts = lib_linked_opts
        self.lib_linked = "-L{0} -l{1} {2}".format(
            self.outputDir, self.name, self._get_str_linked_opts(self.lib_linked_opts)
        )

    def _get_str_linked_opts(self, opts):
        if isinstance(opts, str):
            return opts
        elif isinstance(opts, list):
            return " ".join(opts)
        else:
            return ""

    def setRebuild(self, rebuild: bool):
        self.rebuild = rebuild

    def rebuildByCheckStr(self, checkStr: str):
        hs = hashlib.md5(checkStr.encode())
        cksumfile = Path(self.outputDir / Path("lib" + self.name + ".cksum"))
        hexstr = hs.hexdigest()
        oldHash = ""
        if cksumfile.exists():
            cksumfile = open(str(cksumfile), "r+")
            oldHash = cksumfile.read()
        else:
            cksumfile = open(str(cksumfile), "w")

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
        self.module_name = ""
        self.staticLib = staticLib
        self.orden = 0 if staticLib == None else staticLib.orden

    def isEmpty(self):
        if not self.srcs and not self.incs and not self.staticLib:
            return True
        else:
            return False

    def getDirs(self):
        dirs = []
        for src in self.srcs:
            dirs.append(Path(str(src)).parent)
        dirs = sorted(set(dirs), key=str)
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

    def addGeneralOpt(self, opts: list):
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
        wk = {K.MOD_WORKSPACE: self.modDir, K.MOD_COMPILER_OPTS: self.gCompOpts.opts}
        return wk

    def getAllSrcsC(self):
        return self.getAllSrcs(SrcType.C)

    def getAllSrcs(self, srcType: List[str]):
        srcs = []
        for ext in srcType:
            srcs += list(Path(self.modDir).rglob("*" + ext))
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

    def getAllIncs(self, incType: List[str]):
        incsfiles = []
        for ext in incType:
            incsfiles += list(Path(self.modDir).rglob("*" + ext))

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

    def __init__(self) -> None:
        super().__init__()
        self.module_name = self.get_module_name()
        self.path = self.get_path()
        self.dir = Path(self.path).parent
        _mod = sys.modules.get(self.__module__)
        _proj_root = getattr(_mod, '_project_root', None) if _mod is not None else None
        # Use the logical (non-symlink-resolved) path so that modules inside
        # symlinked directories (e.g. TARGET/ → foreign project sources) remain
        # relative to the workspace root instead of their real filesystem location.
        _src_file_logical = Path(self.path).absolute()
        _src_file = _src_file_logical
        if _proj_root is None:
            # Class defined in a helper module (e.g. pym.py via module()).
            # Fall back: find a dynamically-loaded mk.py module in sys.modules whose
            # __file__ matches self.path.
            _path_str = str(_src_file)
            for _m in sys.modules.values():
                if getattr(_m, '__file__', None) == _path_str:
                    _proj_root = getattr(_m, '_project_root', None)
                    if _proj_root is not None:
                        break
        if _proj_root is not None:
            self.module_path = str(_src_file.parent.relative_to(_proj_root)) + "/"
        else:
            log.debug(
                "project root not set; module_path not available outside read_module context"
            )
            raise Exception("project root not set; module_path not available outside read_module context")

    def get_module_name(self) -> str:
        """Module name

        Returns:
            str: name of module (default: class name)
        """
        return self.__class__.__name__

    def get_path(self) -> str:
        """Get path of module in filesystem

        Returns:
            str: path (default: self.__module__.module_name)
        """
        return f"{self.__module__}.{self.module_name}"

    def init(self) -> Optional["StaticLibrary"]:
        """Initialization of module.

        Override to perform setup before sources are collected.
        Return a :class:`StaticLibrary` instance to declare a static-library
        dependency; return ``None`` (default) for regular modules.

        Returns:
            Optional[StaticLibrary]: static library descriptor, or None
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

    def findSrcs(self, src_type: List[str]) -> List[Path]:
        """Util method for find sources in module path

        Args:
            src_type (List[str]): File extensions to search for — use
                :class:`SrcType` constants (e.g. ``SrcType.C``, ``SrcType.CPP``).

        Returns:
            List[Path]: source file paths found under the module directory
        """
        log.debug(f"find srcs in {self.dir}")
        srcs = []
        for ext in src_type:
            srcs += list(Path(self.dir).rglob("*" + ext))
        return srcs

    def findIncs(self, inc_type: List[str]) -> List[Path]:
        """Util method for find includes in module path

        Args:
            inc_type (List[str]): File extensions to search for — use
                :class:`IncType` constants (e.g. ``IncType.C``, ``IncType.CPP``).

        Returns:
            List[Path]: unique include directory paths found under the module directory
        """
        incsfiles = []
        for ext in inc_type:
            incsfiles += list(Path(self.dir).rglob("*" + ext))

        incs = []
        for i in incsfiles:
            incs.append(i.parent)

        incs = list(dict.fromkeys(incs))
        return incs

    def getCompilerOpts(self) -> Optional[dict]:
        """Get per-module compiler options.

        Override to return a compiler-options dict that is merged with the
        project-level options for sources in this module only.  Return
        ``None`` (default) to apply no extra options.

        Returns:
            Optional[dict]: compiler options dict, or None
        """
        pass

    # ------------------------------------------------------------------
    # New high-level helpers (preferred API)
    # ------------------------------------------------------------------

    def discover_srcs(self, src_type: Optional[List[str]] = None) -> List[str]:
        """Auto-discover sources under the module directory, return project-relative strings.

        Args:
            src_type: Extensions to search for. Defaults to
                :attr:`SrcType.C_AND_ASM` (C + Assembly).

        Returns:
            List[str]: project-relative source paths (e.g. ``['app/main.c', 'app/isr.s']``).
        """
        if src_type is None:
            src_type = SrcType.C_AND_ASM
        paths = self.findSrcs(src_type)
        return [self.module_path + str(p.relative_to(self.dir)) for p in paths]

    def discover_incs(self, discover_header_dirs: bool = False) -> List[str]:
        """Return include roots project-relative.

        Args:
            discover_header_dirs: When ``False`` (default), return only ``[module_path]``.
                When ``True``, scan for header files and return their parent
                directories relative to project root.

        Returns:
            List[str]: include roots relative to project root.
        """
        if not self.module_path:
            return []

        if not discover_header_dirs:
            return [self.module_path]

        inc_dirs = self.findIncs(IncType.CPP)
        if not inc_dirs:
            return [self.module_path]

        rel_dirs = []
        for inc_dir in inc_dirs:
            rel_to_module = str(Path(inc_dir).relative_to(self.dir))
            if rel_to_module == ".":
                rel_dirs.append(self.module_path)
            else:
                rel_dirs.append(self.module_path + rel_to_module)

        return list(dict.fromkeys(rel_dirs))

    def srcs_from(self, files: List[str]) -> List[str]:
        """Prefix explicit source filenames with module_path.

        Args:
            files: Source filenames relative to the module directory.

        Returns:
            List[str]: paths prefixed with ``module_path``.
        """
        return [self.module_path + f for f in files]

    def incs_from(self, dirs: Optional[List[str]] = None) -> List[str]:
        """Prefix explicit include directories with module_path.

        Args:
            dirs: Include directories relative to the module directory.
                  If ``None``, returns ``[module_path]``.

        Returns:
            List[str]: paths prefixed with ``module_path``.
        """
        if dirs is None:
            return [self.module_path] if self.module_path else []
        return [
            self.module_path if d in (".", "") else self.module_path + d
            for d in dirs
        ]

    # ------------------------------------------------------------------
    # Deprecated helpers kept for backward compatibility
    # ------------------------------------------------------------------

    def getAllSrcsC(self) -> List[Path]:
        """Deprecated: use ``findSrcs(SrcType.C)`` instead."""
        warnings.warn(
            "getAllSrcsC() is deprecated; use findSrcs(SrcType.C) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.findSrcs(SrcType.C)

    def getAllIncsC(self) -> List[Path]:
        """Deprecated: use ``findIncs(IncType.C)`` instead."""
        warnings.warn(
            "getAllIncsC() is deprecated; use findIncs(IncType.C) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.findIncs(IncType.C)
    
    def getSrcsWithPath(self, srcs: List[str]) -> List[str]:
        """Deprecated: use :meth:`srcs_from` instead."""
        warnings.warn(
            "getSrcsWithPath() is deprecated; use srcs_from() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.srcs_from(srcs)

    def getIncsWithPath(self, incs: Optional[List[str]] = None) -> List[str]:
        """Deprecated: use :meth:`incs_from` instead."""
        warnings.warn(
            "getIncsWithPath() is deprecated; use incs_from() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.incs_from(incs)


class StaticLibraryModule(metaclass=ABCMeta):

    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, "get_lib_name")
            and callable(subclass.get_lib_name)
            and hasattr(subclass, "get_lib_outputdir")
            and callable(subclass.get_lib_outputdir)
        )

    def decorate_module(self):
        self.name = self.get_lib_name()
        self.lib_name = "lib" + self.name + ".a"
        self.output_dir = Path(self.get_lib_outputdir())
        self.orden = self.get_order()
        self.rebuild = self.get_rebuild()
        self.key = self.name.upper()
        self.library = self.output_dir / Path(self.lib_name)
        self.objects = self.get_objects(self.key)
        self.rule = self.get_rule(self.key)
        self.command = self.get_command(self.key)
        self.linker = self.get_linker(self.key)

    def _get_str_linked_opts(self, opts):
        if isinstance(opts, str):
            return opts
        elif isinstance(opts, list):
            return " ".join(opts)
        else:
            return ""

    @abstractmethod
    def get_lib_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_lib_outputdir(self) -> str:
        raise NotImplementedError

    def get_linker_opts(self) -> str:
        return None

    def get_objects(self, key) -> str:
        return f"{key}_OBJECTS = $({key}_CSRC:%.c=$({key}_OUTPUT)/%.o) $({key}_CSRC:%.s=$({key}_OUTPUT)/%.o)"

    def get_rule(self, key) -> str:
        return f'$({key}_OUTPUT)/%.o: %.c\n\t$(call logger-compile-lib,"CC","{key}",$<)\n\t@mkdir -p $(dir $@)\n\t$(CC) $(CFLAGS) $(INCS) -o $@ -c $<'

    def get_command(self, key) -> str:
        return f'$({key}_AR): $({key}_OBJECTS)\n\t$(call logger-compile,"AR",$@)\n\t$(AR) -rc $@ $(filter %.o,$({key}_OBJECTS))'

    def get_linker(self, key) -> str:
        return "-L{0} -l{1} {2}".format(
            self.output_dir,
            self.name,
            self._get_str_linked_opts(self.get_linker_opts()),
        )

    def get_order(self):
        return 1

    def get_rebuild(self):
        return False


class POJOModule(AbstractModule):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.includes = []
        self.sources = []
        self.compiler_opts = None
        self.init_resp = None

    def init(self):
        return self.init_resp

    def getSrcs(self) -> list:
        return self.includes

    def getIncs(self) -> list:
        return self.sources

    def getCompilerOpts(self):
        return self.compiler_opts

    def get_path(self):
        return self.path


class BasicCModule(AbstractModule):
    """Basic C module — auto-discovers C and Assembly sources; includes module directory.

    Args:
        path (str): path to module, _mk.py file.
    """

    def __init__(self):
        super().__init__()

    def getSrcs(self) -> List[str]:
        """Return all C and Assembly sources, project-relative.

        Returns:
            List[str]: project-relative source paths.
        """
        return self.discover_srcs()

    def getIncs(self) -> List[str]:
        """Return discovered include roots, project-relative.

        Returns:
            List[str]: include directories inferred from headers (fallback: ``[module_path]``).
        """
        return self.discover_incs(discover_header_dirs=True)


class BasicCppModule(AbstractModule):
    """Basic C++ module — auto-discovers C++, C and Assembly sources; includes module directory.

    Subclass this (or use @ModuleClass) for C++ source directories.
    Override getSrcs() or getIncs() for custom file selection.

    Args:
        path (str): path to module, _mk.py or .mk.py file.
    """

    def __init__(self):
        super().__init__()

    def getSrcs(self) -> List[str]:
        """Return all C++ and Assembly sources, project-relative.

        Returns:
            List[str]: project-relative source paths.
        """
        return self.discover_srcs(SrcType.CPP_AND_ASM)

    def getIncs(self) -> List[str]:
        """Return module directory as include root, project-relative.

        Returns:
            List[str]: ``[module_path]``.
        """
        return self.discover_incs()


class ExternalModule(AbstractModule):
    """The ExternalModule object that inherits from AbstractModule for include external pymaketool module

    Args:
        path (str): path to module, _mk.py file.

    Attributes:
        remoteModule (AbstractModule): remote module object.

    Raises:
            AttributeError: path is not valid
    """

    def __init__(self):
        super().__init__()
        try:
            modPath = self.getModulePath()
            _name = Path(modPath).name
            if not (_name == "mk.py" or _name.endswith("_mk.py") or _name.endswith(".mk.py")):
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
    def getModulePath(self) -> str:
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
        log.debug(f"class '{clazz.__name__}' is inheritance of Module.AbstractModule")
    else:
        log.warning(
            f"class '{clazz.__name__}' in '{__name__}' not inheritance of Module.AbstractModule"
        )

    # classdir = str(clazz)
    # log.debug(f"class dir {classdir}")
    # m = re.search(r"<class \'(?P<dir>[a-zA-Z\./_-]+)\'>", classdir)
    # modulePath = None
    # if m:
    #     p = Path(m.group('dir'))
    #     modulePath = p
    # modulePath = f"{clazz.__module__}.{clazz.__name__}"

    obj = clazz()
    global ModulesInstances
    try:
        _ = ModulesInstances
    except NameError:
        log.debug(f"create global modules list")
        ModulesInstances = []

    log.debug(
        f"add new instance of ModuleClass '{clazz.__name__}' with path {clazz.__module__}"
    )
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
