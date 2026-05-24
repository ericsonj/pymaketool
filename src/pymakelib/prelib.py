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
import re
import warnings as _warnings
from pymakelib.preutil import copyFile, getFileHash
from . import AbstractMake
from typing import List
import sys
from pathlib import Path
import importlib.util
from . import preconts as K
from . import Define as D
from .module import ModuleHandle
from .module import CompilerOptions
from .module import Module, getModuleInstance, cleanModuleInstance, AbstractModule, POJOModule
from .module import StaticLibrary
from . import getProjectInstance
from . import Logger

log = Logger.getLogger()

def add_value2list(dstList: list, values):
    if isinstance(values, list):
        for item in values:
            dstList.append(item)
    elif isinstance(values, dict):
        for keys in values:
            if isinstance(values[keys], list):
                for item in values[keys]:
                    dstList.append(item)
            else:
                dstList.append(values[keys])
    else:
        dstList.append(values)

def wprInit(mod, modHandle, moduleInstance=None):
    try:
        if moduleInstance:
            return moduleInstance.init()
        else:
            return getattr(mod, K.MOD_F_INIT)(modHandle)
    except AttributeError as ae:
        log.debug(ae)
    except Exception as ex:
        log.exception(ex)
        exit(-1)

def wprGetSrcs(mod, modHandle, moduleInstance=None):
    try:
        if moduleInstance:
            return moduleInstance.getSrcs()
        else:
            return getattr(mod, K.MOD_F_GETSRCS)(modHandle)
    except AttributeError as ae:
        log.warning(ae)
    except Exception as ex:
        log.exception(ex)
        exit(-1)

def wprGetIncs(mod, modHandle, moduleInstance=None):
    try:
        if moduleInstance:
            return moduleInstance.getIncs()
        else:
            return getattr(mod, K.MOD_F_GETINCS)(modHandle)
    except AttributeError as ae:
        log.warning(ae)
    except Exception as ex:
        log.exception(ex)
        exit(-1)

def wprGetCompilerOpts(mod, modHandle, moduleInstance=None):
    try:
        if moduleInstance:
            return moduleInstance.getCompilerOpts()
        else:
            return getattr(mod, K.MOD_F_GETCOMPILEROPTS)(modHandle)
    except AttributeError as ae:
        log.debug(ae)
    except Exception as ex:
        log.exception(ex)
        exit(-1)


def tmp_file_name(file_path: str):
    return f"{file_path}~"


def overrideFile(outfile):
    if not Path(outfile).exists():
        copyFile(tmp_file_name(outfile), outfile)
        return
    outfile_hash = getFileHash(outfile)
    tmp_outfile_hash = getFileHash(tmp_file_name(outfile))
    if (outfile_hash != tmp_outfile_hash):
        copyFile(tmp_file_name(outfile), outfile)


def readGenHeader(headerpath):
    lib = importlib.util.spec_from_file_location(str(headerpath), str(headerpath))
    mod = importlib.util.module_from_spec(lib)
    log.debug(f"exec code generator {mod.__name__}")
    outfile = str(headerpath)
    outfile = outfile.replace('_h.py', '.h')
    outfile = outfile.replace('.h.py', '.h')
    log.debug(f"output file {outfile}")
    stdout_ = sys.stdout #Keep track of the previous value.
    sys.stdout = open(tmp_file_name(outfile), 'w') # Something here that provides a write method.
    lib.loader.exec_module(mod)
    sys.stdout.close()
    sys.stdout = stdout_
    overrideFile(outfile)
    os.remove(tmp_file_name(outfile))


def read_module(module_path: Path, compiler_opts, goals=None, project_root: Path | None = None) -> List[AbstractModule]:
    lib = importlib.util.spec_from_file_location(str(module_path), str(module_path))
    if lib is None:
        raise ImportError(f"Could not load module from {module_path}")
    mod = importlib.util.module_from_spec(lib)
    setattr(mod, '_project_root', project_root)
    sys.modules[mod.__name__] = mod
    log.debug(f"exec module {mod.__name__}")
    try:
        lib.loader.exec_module(mod)
    finally:
        sys.modules.pop(mod.__name__, None)
    
    moduleInstances = getModuleInstance()
    modules = []

    if not moduleInstances:
        has_any_fn = any(hasattr(mod, fn) for fn in [
            K.MOD_F_GETSRCS, K.MOD_F_GETINCS, K.MOD_F_INIT, K.MOD_F_GETCOMPILEROPTS
        ])

        if not has_any_fn:
            # Empty file: behave like module() — auto-discover .c/.h in dir
            from .module import BasicCModule, ModuleClass
            import pymakelib.prelib as _prelib_mod
            _prelib_mod._project_root = project_root
            try:
                @ModuleClass
                class _AutoDiscover(BasicCModule):
                    def get_path(_self):
                        return str(module_path)
                modules.extend(getModuleInstance())
                cleanModuleInstance()
            finally:
                del _prelib_mod._project_root
        else:
            # Legacy free-function pattern
            _warnings.warn(
                f"[pymaketool] {module_path.name}: free-function module pattern "
                "(getSrcs/getIncs at module level) is deprecated. "
                "Use 'from pymakelib.pym import module; module()' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            modHandle = ModuleHandle(module_path.parent, compiler_opts, goals)
            m = POJOModule(module_path)
            m.init_resp = wprInit(mod, modHandle)
            m.includes = wprGetIncs(mod, modHandle)
            m.sources = wprGetSrcs(mod, modHandle)
            m.compiler_opts = wprGetCompilerOpts(mod, modHandle)
            modules.append(m)
            cleanModuleInstance()
    else:
        modules.extend(getModuleInstance())
        cleanModuleInstance()

    return modules


def readModule(modPath, compilerOpts, goals=None, project_root: Path | None = None):
    lib = importlib.util.spec_from_file_location(str(modPath), str(modPath))
    mod = importlib.util.module_from_spec(lib)
    mod._project_root = project_root
    sys.modules[mod.__name__] = mod
    log.debug(f"exec module {mod.__name__}")
    try:
        lib.loader.exec_module(mod)
    finally:
        sys.modules.pop(mod.__name__, None)

    moduleInstances = getModuleInstance()
    modules = []

    if not moduleInstances:
        has_any_fn = any(hasattr(mod, fn) for fn in [
            K.MOD_F_GETSRCS, K.MOD_F_GETINCS, K.MOD_F_INIT, K.MOD_F_GETCOMPILEROPTS
        ])

        if not has_any_fn:
            # Truly empty file — auto-discover .c/.h in directory
            from .module import BasicCModule, ModuleClass
            import pymakelib.prelib as _prelib_mod
            _prelib_mod._project_root = project_root
            try:
                @ModuleClass
                class _AutoDiscover(BasicCModule):
                    def get_path(_self):
                        return str(modPath)
                instance = getModuleInstance()[0]
                cleanModuleInstance()
            finally:
                del _prelib_mod._project_root
            srcs = []
            incs = []
            result = wprGetSrcs(None, None, instance)
            if result:
                add_value2list(srcs, result)
            result = wprGetIncs(None, None, instance)
            if result:
                add_value2list(incs, result)
            modules.append(Module(srcs, incs, [], modPath))
            return modules

        modHandle = ModuleHandle(modPath.parent, compilerOpts, goals)
        srcs = []
        incs = []
        flags = []
        staticLib = None
        # init attribute is not mandatory
        result = wprInit(mod, modHandle)
        if isinstance(result, StaticLibrary):
            log.debug(f"\'{mod.__name__}\' is static library")
            staticLib = result

        result = wprGetSrcs(mod, modHandle)
        if result:
            add_value2list(srcs, result)
        else:
            log.debug(f"\'{mod.__name__}\' return empty sources")

        result = wprGetIncs(mod, modHandle)
        if result:
            add_value2list(incs, result)
        else:
            log.debug(f"\'{mod.__name__}\' return empty includes")

        result = wprGetCompilerOpts(mod, modHandle)
        if issubclass(type(result), CompilerOptions):
            result = result.opts
        if result:
            flags.append(result)
        else:
            log.debug(
                f"\'{mod.__name__}\' return empty compiler options")

        modules.append(Module(srcs, incs, flags, modPath, staticLib=staticLib))
        return modules

    for moduleInstance in moduleInstances:

        modHandle = ModuleHandle(modPath.parent, compilerOpts, goals)

        srcs = []
        incs = []
        flags = []
        staticLib = None

        if moduleInstance:
            log.info(f"read ModuleClass \'{mod.__name__}:{type(moduleInstance).__name__}\'")

        # init attribute is not mandatory
        result = wprInit(mod, modHandle, moduleInstance)
        if isinstance(result, StaticLibrary):
            log.debug(f"\'{type(moduleInstance).__name__}\' is static library")
            staticLib = result

        result = wprGetSrcs(mod, modHandle, moduleInstance)
        if result:
            add_value2list(srcs, result)
        else:
            log.debug(f"\'{type(moduleInstance).__name__}\' return empty sources")

        result = wprGetIncs(mod, modHandle, moduleInstance)
        if result:
            add_value2list(incs, result)
        else:
            log.debug(f"\'{type(moduleInstance).__name__}\' return empty includes")

        result = wprGetCompilerOpts(mod, modHandle, moduleInstance)
        if issubclass(type(result), CompilerOptions):
            result = result.opts
        if result:
            flags.append(result)
        else:
            log.debug(
                f"\'{type(moduleInstance).__name__}\' return empty compiler options")

        m = Module(srcs, incs, flags, modPath, staticLib=staticLib)
        if moduleInstance.module_name:
            m.module_name = moduleInstance.module_name
        modules.append(m)

    cleanModuleInstance()

    return modules


def _deps_to_str(deps) -> str:
    if isinstance(deps, list):
        return ' '.join(deps)
    elif isinstance(deps, str):
        return deps
    return ''


def _script_to_lines(script) -> list:
    if isinstance(script, list):
        return script
    elif isinstance(script, str):
        return [script]
    return []


def list2str(l):
    return ' '.join(l)


_VALID_C_IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
_ALLOWED_MACRO_TYPES = (type(None), str, bool, int, D)

def _validate_macros(macros: dict) -> None:
    for key, value in macros.items():
        if not _VALID_C_IDENT.match(key):
            raise ValueError(
                f"Invalid macro key {key!r}: must be a valid C identifier "
                f"(letters, digits, underscores; cannot start with a digit)."
            )
        if not isinstance(value, _ALLOWED_MACRO_TYPES):
            raise TypeError(
                f"Macro {key!r} has unsupported value type {type(value).__name__!r}. "
                f"Allowed: None (flag), str, bool, int, Define."
            )

def macrosDictToString(macros):
    if not isinstance(macros, dict):
        return ''
    _validate_macros(macros)
    mstr = []
    for key in macros:
        if macros[key] != None and macros[key] != '':
            if isinstance(macros[key], str):
                val = macros[key]
                quoted = '\\\"{}\\\"'.format(val)
                if ' ' in val:
                    quoted = "'\\\"{}\\\"'".format(val)
                mstr.append('-D{}={}'.format(key, quoted))
            elif isinstance(macros[key], bool):
                mstr.append(
                    '-D{}={}'.format(key, '1' if macros[key] else '0'))
            elif isinstance(macros[key], D):
                define_val = macros[key].getDefine()
                if ' ' in define_val:
                    mstr.append("-D{}='{}'".format(key, define_val))
                else:
                    mstr.append('-D{}={}'.format(key, define_val))
            else:
                mstr.append('-D{}={}'.format(key, macros[key]))
        else:
            mstr.append('-D{}'.format(key))

    return ' '.join(mstr)


def compilerOptsByModuleToLine(compOpts):
    mstr = []
    for moduleCompileOps in compOpts:
        if isinstance(moduleCompileOps, dict):
            for key in moduleCompileOps:
                if key == 'TARGETS':
                    continue
                if (key == K.COMPOPTS_MACROS_KEY and isinstance(moduleCompileOps[key], dict)):
                    macros = macrosDictToString(moduleCompileOps[key])
                    mstr.append(macros)
                else:
                    mstr.append(list2str(moduleCompileOps[key]))

        elif isinstance(moduleCompileOps, list):
            for item in moduleCompileOps:
                mstr.append(item)
    rmstr = list(filter(lambda item: item, mstr))
    rmstr = ' '.join(rmstr)
    rmstr = ' '.join(rmstr.split())
    log.debug(f"compiler options: {rmstr}")
    return rmstr


def read_Makefilepy_obj(workpath='') -> AbstractMake:
    makefilepy_path = workpath + K.MAKEFILE_PY
    lib = importlib.util.spec_from_file_location(makefilepy_path, makefilepy_path)
    mod = importlib.util.module_from_spec(lib)
    lib.loader.exec_module(mod)
    projectInstance = getProjectInstance()
    if not projectInstance:
        class bproject(AbstractMake):
            def getProjectSettings(self, **kwargs) -> dict:
                return getattr(mod, K.MK_F_GETPROJECTSETTINGS)()
            def getCompilerSet(self, **kwargs) -> dict:
                return getattr(mod, K.MK_F_GETCOMPILERSET)()
            def getCompilerOpts(self, **kwargs) -> dict:
                return getattr(mod, K.MK_F_GETCOMPILEROPTS)()
            def getLinkerOpts(self, **kwargs) -> dict:
                return getattr(mod, K.MK_F_GETLINKEROPTS)()
            def getTargetsScript(self, **kwargs) -> dict:
                return getattr(mod, K.MK_F_GETTARGETSSCRIPT)()
            def getPhonyTargets(self) -> dict:
                fn = getattr(mod, K.MK_F_GETPHONYTARGETS, None)
                return fn() if fn else {}
        projectInstance = bproject()
    return projectInstance


def resolve_config_dir(project_root: Path) -> tuple:
    """Detect whether the project uses the new subdirectory layout or the legacy root layout.

    Returns (config_dir: Path, mode: str) where mode is 'subdir' or 'legacy'.
    Raises FileNotFoundError if Makefile.py cannot be found in either location.
    """
    import warnings
    for candidate in K.MAKEFILE_SUBDIR_CANDIDATES:
        subdir = project_root / candidate
        if (subdir / K.MAKEFILE_PY).exists():
            return subdir, 'subdir'
    if (project_root / K.MAKEFILE_PY).exists():
        warnings.warn(
            f"\n[pymaketool] Makefile.py found at project root (legacy layout).\n"
            f"  This layout is deprecated. Consider moving your build config into a "
            f"pymake/ subdirectory.\n"
            f"  See: https://github.com/ericsonj/pymaketool",
            DeprecationWarning,
            stacklevel=3,
        )
        return project_root, 'legacy'
    raise FileNotFoundError(
        f"No {K.MAKEFILE_PY} found in project root or known subdirectories "
        f"{K.MAKEFILE_SUBDIR_CANDIDATES}."
    )


def read_Makefilepy(workpath='', config_dir: Path | None = None):
    if config_dir is not None:
        makefilepy_path = str(config_dir / K.MAKEFILE_PY)
    else:
        makefilepy_path = workpath + K.MAKEFILE_PY
    lib = importlib.util.spec_from_file_location(makefilepy_path, makefilepy_path)
    mod = importlib.util.module_from_spec(lib)
    lib.loader.exec_module(mod)

    projectInstance = getProjectInstance()
    if projectInstance:
        log.info("makeclass define")

    def wprGetProjectSettings():
        try:
            if projectInstance:
                return projectInstance.getProjectSettings()
            else:
                return getattr(mod, K.MK_F_GETPROJECTSETTINGS)()
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def wprGetCompilerSet():
        try:
            if projectInstance:
                return projectInstance.getCompilerSet()
            else:
                return getattr(mod, K.MK_F_GETCOMPILERSET)()
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def wprGetCompileOpts():
        try:
            if projectInstance:
                return projectInstance.getCompilerOpts()
            else:
                return getattr(mod, K.MK_F_GETCOMPILEROPTS)()
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def wprGetLinkerOpts():
        try:
            if projectInstance:
                return projectInstance.getLinkerOpts()
            else:
                return getattr(mod, K.MK_F_GETLINKEROPTS)()
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def wprGetTargetScript():
        try:
            if projectInstance:
                return projectInstance.getTargetsScript()
            else:
                return getattr(mod, K.MK_F_GETTARGETSSCRIPT)()
        except Exception as ex:
            log.exception(ex)
            exit(-1)

    def wprGetPhonyTargets():
        try:
            if projectInstance and hasattr(projectInstance, K.MK_F_GETPHONYTARGETS):
                return projectInstance.getPhonyTargets()
            elif hasattr(mod, K.MK_F_GETPHONYTARGETS):
                return getattr(mod, K.MK_F_GETPHONYTARGETS)()
        except Exception as ex:
            log.exception(ex)
        return {}

    _out_dir = config_dir if config_dir is not None else Path(workpath) if workpath else Path('.')
    makevars = open(_out_dir / K.VARS_MK, 'w')

    # -----------------------------------------------------------------------
    # Lazy imports for typed containers (avoid circular import at module load)
    # -----------------------------------------------------------------------
    def _to_dict_if_typed(obj):
        """Normalize CompilerOpts/LinkerOpts/ProjectSettings/CompilerSet → dict."""
        return obj.to_dict() if hasattr(obj, 'to_dict') else obj

    def _targets_to_dict(targets):
        """Normalize {name: Target} → {name: dict}."""
        from pymakelib import Target as _Target
        if isinstance(targets, dict):
            result = {}
            for k, v in targets.items():
                result[k] = v.to_dict() if isinstance(v, _Target) else v
            return result
        return targets

    # Known compiler-option dict keys — used by validation phase
    _KNOWN_COMP_KEYS = {
        K.MK_KEY_MACROS, K.MK_KEY_MACHINE_OPTS, K.MK_KEY_OPTIMIZE_OPTS,
        K.MK_KEY_OPTIONS, K.MK_KEY_DEBUGGING_OPTS, K.MK_KEY_PREPROCESSOR_OPTS,
        K.MK_KEY_WARNINGS_OPTS, K.MK_KEY_CONTROL_C_OPTS, K.MK_KEY_GENERAL_OPTS,
        'TARGETS', 'PHONY_TARGETS', 'LIBRARIES',
    }

    projSettings = None
    compSet = None
    compOpts = None

    try:
        projSettings = _to_dict_if_typed(wprGetProjectSettings())
        if projSettings[K.PROJSETT_PROJECTNAME]:
            makevars.write('{0:<15} = {1}\n'.format(
                'PROJECT', projSettings[K.PROJSETT_PROJECTNAME]))
        if projSettings[K.PROJSETT_FOLDEROUT]:
            projSettings[K.PROJSETT_FOLDEROUT] = Path(
                projSettings[K.PROJSETT_FOLDEROUT])
            makevars.write('{0:<15} = {1}\n'.format(
                'PROJECT_OUT', projSettings[K.PROJSETT_FOLDEROUT]))
    except Exception as e:
        log.exception(e)

    makevars.write('\n')

    try:
        compSet = _to_dict_if_typed(wprGetCompilerSet())
        for sfx in (
            K.COMPILERSET_CC,
            K.COMPILERSET_CXX,
            K.COMPILERSET_LD,
            K.COMPILERSET_AR,
            K.COMPILERSET_AS,
            K.COMPILERSET_OBJCOPY,
            K.COMPILERSET_SIZE,
            K.COMPILERSET_OBJDUMP,
            K.COMPILERSET_NM,
            K.COMPILERSET_RANLIB,
            K.COMPILERSET_STRINGS,
            K.COMPILERSET_STRIP,
            K.COMPILERSET_CXXFILT,
            K.COMPILERSET_ADDR2LINE,
            K.COMPILERSET_READELF,
            K.COMPILERSET_ELFEDIT
        ):
            if compSet[sfx]:
                makevars.write('{0:<10} := {1}\n'.format(sfx, compSet[sfx]))
    except KeyError as ke:
        log.debug(f"not found compiler option {ke}")
    except Exception as e:
        log.exception(e)

    makevars.write('\n')

    try:
        compOpts = _to_dict_if_typed(wprGetCompileOpts())
        # Phase 5: warn on unknown keys (only for raw-dict path; typed path already validates)
        if isinstance(compOpts, dict):
            for _k in compOpts:
                if _k not in _KNOWN_COMP_KEYS:
                    _warnings.warn(
                        f"[pymaketool] getCompilerOpts(): unknown key '{_k}'. "
                        f"Known keys: {sorted(_KNOWN_COMP_KEYS)}. "
                        "Use CompilerOpts dataclass for type safety.",
                        UserWarning,
                        stacklevel=2,
                    )
        if isinstance(compOpts, dict):
            for key in compOpts:
                makevars.write('# {0}\n'.format(key))
                if (key == 'MACROS' and isinstance(compOpts[key], dict)):
                    makevars.write(
                        'COMPILER_FLAGS += {}\n'.format(macrosDictToString(compOpts[key])))
                else:
                    makevars.write(
                        'COMPILER_FLAGS += {}\n'.format(list2str(compOpts[key])))
        elif isinstance(compOpts, list):
            for item in compOpts:
                makevars.write('COMPILER_FLAGS += {}\n'.format(item))
        else:
            log.debug("Not load getCompilerOpts")
    except Exception as ex:
        log.exception(ex)

    makevars.write('\n')

    try:
        linkOpts = _to_dict_if_typed(wprGetLinkerOpts())
        if isinstance(linkOpts, dict):
            for keys in linkOpts:
                makevars.write('# {0}\n'.format(keys))
                makevars.write(
                    'LDFLAGS += {}\n'.format(list2str(linkOpts[keys])))
        elif isinstance(linkOpts, list):
            for item in linkOpts:
                makevars.write('LDFLAGS += {}\n'.format(item))
    except Exception as ex:
        log.exception(ex)

    makevars.close()

    targetsmk = open(_out_dir / K.TARGETS_MK, 'w')

    try:
        targets = _targets_to_dict(wprGetTargetScript())
        if isinstance(targets, dict):
            if len(targets) == 0:
                pass
            else:
                labels = []
                targetval = []
                targetsct = []
                logkeys = []
                for k in targets:
                    labels.append(k)
                    targetval.append(targets[k]['FILE'])
                    targetsct.append(targets[k]['SCRIPT'])
                    if 'LOGKEY' in targets[k]:
                        logkeys.append(targets[k]['LOGKEY'])
                    else:
                        logkeys.append('>>')

                # print labels
                for i in range(len(targetval)):
                    targetsmk.write("{0:<15} = {1}\n".format(
                        labels[i], targetval[i]))

                targetsmk.write('\nTARGETS = $({})\n\n'.format(
                    labels[len(targetval)-1]))

                for i in range(len(labels)):
                    if labels[i] == 'TARGET':
                        targetsmk.write("\n$({}): {} {}\n".format(
                            labels[i], '$(OBJECTS) $(SLIBS_OBJECTS)', '' if i == 0 else "$("+ labels[i-1] + ")"))
                    else:
                        targetsmk.write("\n$({}): {}\n".format(
                            labels[i], '' if i == 0 else "$("+ labels[i-1] + ")"))

                    targetsmk.write(
                        '\t$(call logger-compile,"{}",$@)\n'.format(logkeys[i]))
                    script = targetsct[i]
                    script = ' '.join(script)
                    targetsmk.write('\t{}\n'.format(script))

                targetsmk.write('\n')

                targetsmk.write("\n{}:\n".format('clean_targets'))
                targetlist = ('$('+l+')' for l in labels)
                targetsmk.write('\trm -rf {}\n'.format(' '.join(targetlist)))
                if compOpts:
                    compOpts['TARGETS'] = targets
    except Exception as e:
        log.exception(e)

    try:
        phony_targets = wprGetPhonyTargets()
        if isinstance(phony_targets, dict) and phony_targets:
            names = ' '.join(phony_targets.keys())
            targetsmk.write(f"\n.PHONY: {names}\n")
            for name, cfg in phony_targets.items():
                deps = _deps_to_str(cfg.get('deps', []))
                logkey = cfg.get('logkey', name.upper())
                script_lines = _script_to_lines(cfg.get('script', []))
                targetsmk.write(f"\n{name}: {deps}\n")
                targetsmk.write(f'\t$(call logger-compile,"{logkey}",$@)\n')
                for i, cmd in enumerate(script_lines):
                    if i < len(script_lines) - 1:
                        targetsmk.write(f"\t{cmd} \\\n")
                    else:
                        targetsmk.write(f"\t{cmd}\n")
            if compOpts and isinstance(compOpts, dict):
                compOpts['PHONY_TARGETS'] = phony_targets
    except Exception as e:
        log.exception(e)

    targetsmk.close()

    return projSettings, compOpts, compSet
