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

import sys
from pathlib import Path
import importlib.util
from . import preconts as K
from . import Define as D
from .module import ModuleHandle
from .module import CompilerOptions
from .module import Module, getModuleInstance, cleanModuleInstance
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

def reafGenHeader(headerpath):
    lib = importlib.util.spec_from_file_location(str(headerpath), str(headerpath))
    mod = importlib.util.module_from_spec(lib)
    log.debug(f"exec code generator {mod.__name__}")
    outfile = str(headerpath)
    outfile = outfile.replace('_h.py', '.h')
    outfile = outfile.replace('.h.py', '.h')
    log.debug(f"output fiel {outfile}")
    stdout_ = sys.stdout #Keep track of the previous value.
    sys.stdout = open(outfile, 'w') # Something here that provides a write method.
    lib.loader.exec_module(mod)
    sys.stdout = stdout_


def readModule(modPath, compilerOpts, goals=None):
    lib = importlib.util.spec_from_file_location(str(modPath), str(modPath))
    mod = importlib.util.module_from_spec(lib)
    log.debug(f"exec module {mod.__name__}")
    lib.loader.exec_module(mod)

    moduleInstances = getModuleInstance()
    modules = []

    if not moduleInstances:
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

        modules.append(Module(srcs, incs, flags, modPath, staticLib=staticLib))

    cleanModuleInstance()

    return modules


def list2str(l):
    return ' '.join(l)


def macrosDictToString(macros):
    mstr = []
    if isinstance(macros, dict):
        for key in macros:
            if macros[key] != None and macros[key] != '':
                if isinstance(macros[key], str):
                    mstr.append('-D{}=\\\"{}\\\"'.format(key, macros[key]))
                elif isinstance(macros[key], bool):
                    mstr.append(
                        '-D{}={}'.format(key, '1' if macros[key] else '0'))
                elif isinstance(macros[key], D):
                    mstr.append(
                        '-D{}={}'.format(key, macros[key].getDefine()))
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


def read_Makefilepy(workpath=''):
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

    makevars = open(K.VARS_MK, 'w')

    projSettings = None
    compSet = None
    compOpts = None

    try:
        projSettings = wprGetProjectSettings()
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
        compSet = wprGetCompilerSet()
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
        compOpts = wprGetCompileOpts()
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
        linkOpts = wprGetLinkerOpts()
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

    targetsmk = open('targets.mk', 'w')

    try:
        targets = wprGetTargetScript()
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

                for i in range(len(targetval)):
                    targetsmk.write("{0:<15} = {1}\n".format(
                        labels[i], targetval[i]))

                targetsmk.write('\nTARGETS = $({})\n\n'.format(
                    labels[len(targetval)-1]))

                for i in range(len(labels)):
                    if labels[i] == 'TARGET':
                        targetsmk.write("\n$({}): {}\n".format(
                            labels[i], '$(OBJECTS) $(SLIBS_OBJECTS)'))
                    else:
                        targetsmk.write("\n$({}): $({})\n".format(
                            labels[i], labels[i-1]))

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

    targetsmk.close()

    return projSettings, compOpts, compSet
