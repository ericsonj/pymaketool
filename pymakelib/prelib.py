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

from pathlib import Path
import importlib.util
from . import preconts as K
from . import D
from .Module import ModuleHandle
from .Module import CompilerOptions
from .Module import Module
from .Module import StaticLibrary

def addToList(dstList: list, values):
    if isinstance(values, list):
        for item in values:
            dstList.append(item)
    elif isinstance(values, dict):
        for keys in values:
            for item in values[keys]:
                dstList.append(item)
    else:
        dstList.append(values)


def readModule(modPath, compilerOpts, goals=None):
    lib = importlib.util.spec_from_file_location(str(modPath), str(modPath))
    mod = importlib.util.module_from_spec(lib)
    lib.loader.exec_module(mod)
    
    modHandle = ModuleHandle(modPath.parent, compilerOpts, goals)
    
    srcs = []
    incs = []
    flags = []
    staticLib = None

    try:
        result = getattr(mod, K.MOD_F_INIT)(modHandle)
        if isinstance(result, StaticLibrary):
            staticLib = result
    except:
        pass

    try:
        result = getattr(mod, K.MOD_F_GETSRCS)(modHandle)
        addToList(srcs, result)
    except:
        pass

    try:
        result = getattr(mod, K.MOD_F_GETINCS)(modHandle)
        addToList(incs, result)
    except:
        pass

    try:
        if hasattr(mod, K.MOD_F_GETCOMPILEROPTS):
            result = getattr(mod, K.MOD_F_GETCOMPILEROPTS)(modHandle)
            if issubclass(type(result), CompilerOptions):
                result = result.opts
            flags.append(result)
    except Exception as e:
        print(e)

    return Module(srcs, incs, flags, modPath, staticLib=staticLib)


def getLineSeparator(key: str, num: int):
    header = ''
    for _ in range(num):
        header += key
    return header


def listToString(l):
    aux = ""
    for item in l:
        aux += (str(item) + " ")
    aux.strip()
    return aux


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
                if (key == K.COMPOPTS_MACROS_KEY and isinstance(moduleCompileOps[key], dict)):
                    macros = macrosDictToString(moduleCompileOps[key])
                    mstr.append(macros)
                else:
                    mstr.append(listToString(moduleCompileOps[key]))

        elif isinstance(moduleCompileOps, list):
            for item in moduleCompileOps:
                mstr.append(item)

    return ' '.join(mstr)


def read_Makefilepy():
    lib = importlib.util.spec_from_file_location(K.MAKEFILE_PY, K.MAKEFILE_PY)
    mod = importlib.util.module_from_spec(lib)
    lib.loader.exec_module(mod)

    makevars = open(K.VARS_MK, 'w')

    projSettings = None
    compSet = None
    compOpts = None

    try:
        projSettings = getattr(mod, K.MK_F_GETPROJECTSETTINGS)()
        if projSettings[K.PROJSETT_PROJECTNAME]:
            makevars.write('{0:<15} = {1}\n'.format(
                'PROJECT', projSettings[K.PROJSETT_PROJECTNAME]))
        if projSettings[K.PROJSETT_FOLDEROUT]:
            projSettings[K.PROJSETT_FOLDEROUT] = Path(
                projSettings[K.PROJSETT_FOLDEROUT])
            makevars.write('{0:<15} = {1}\n'.format(
                'PROJECT_OUT', projSettings[K.PROJSETT_FOLDEROUT]))
    except Exception as e:
        print(e)

    makevars.write('\n')

    try:
        compSet = getattr(mod, K.MK_F_GETCOMPILERSET)()
        for sfx in (K.COMPILERSET_CC, K.COMPILERSET_CXX, K.COMPILERSET_LD, K.COMPILERSET_AR, K.COMPILERSET_AS, K.COMPILERSET_OBJCOPY, K.COMPILERSET_SIZE, K.COMPILERSET_OBJDUMP):
            if compSet[sfx]:
                makevars.write('{0:<10} := {1}\n'.format(sfx, compSet[sfx]))
    except:
        pass

    makevars.write('\n')

    try:
        compOpts = getattr(mod, K.MK_F_GETCOMPILEROPTS)()
        if isinstance(compOpts, dict):
            for key in compOpts:
                makevars.write('# {0}\n'.format(key))
                if (key == 'MACROS' and isinstance(compOpts[key], dict)):
                    makevars.write(
                        'COMPILER_FLAGS += {}\n'.format(macrosDictToString(compOpts[key])))
                else:
                    makevars.write(
                        'COMPILER_FLAGS += {}\n'.format(listToString(compOpts[key])))

        elif isinstance(compOpts, list):
            for item in compOpts:
                makevars.write('COMPILER_FLAGS += {}\n'.format(item))
        else:
            print("Not load getCompilerOpts")
    except:
        pass

    makevars.write('\n')

    try:
        linkOpts = getattr(mod, K.MK_F_GETLINKEROPTS)()
        if isinstance(linkOpts, dict):
            for keys in linkOpts:
                makevars.write('# {0}\n'.format(keys))
                makevars.write(
                    'LDFLAGS += {}\n'.format(listToString(linkOpts[keys])))
        elif isinstance(linkOpts, list):
            for item in linkOpts:
                makevars.write('LDFLAGS += {}\n'.format(item))
    except:
        pass

    makevars.close()

    targetsmk = open('targets.mk', 'w')

    try:
        targets = getattr(mod, K.MK_F_GETTARGETSSCRIPT)()
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

    except Exception as e:
        print(e)

    targetsmk.close()

    return projSettings, compOpts, compSet
