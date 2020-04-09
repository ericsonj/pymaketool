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
import inspect
import sys
import os
import time
import subprocess
import json
import re
import copy
from pymakelib import eclipse_cproject as cp
from pymakelib import preconts as K
from pymakelib import prelib as plib
from pymakelib import moduleignore


USE_EXCLUDE_FOLDERS = True

# ------------------------------------------------------
# ------------------------------------------------------
# ------------------------------------------------------


modules = []
modulesPaths = []
ignoreModuleList = []

projSettings, compilerOpts, compilerSettings = plib.read_Makefilepy()


ignoreModuleList = moduleignore.readIgnoreFile()


modulesPaths = list(Path('./').rglob('*[.|_]mk.py'))
# Load modules
for filename in modulesPaths:
    mod = plib.readModule(filename, copy.deepcopy(compilerOpts))
    modules.append(mod)

for ex in ignoreModuleList:
    for i, o in enumerate(modules):
        if o.filename == ex:
            del modules[i]
            break

# Write CSRC
srcsfile = open('srcs.mk', 'w')

includes = []

for mod in modules:
    print('Module: {}'.format(mod.filename))
    srcsfile.write("{}\n".format(plib.getLineSeparator('#', 52)))
    srcsfile.write("#{0:^50}#\n".format(str(mod.filename)))
    srcsfile.write("{}\n".format(plib.getLineSeparator('#', 52)))

    for src in mod.srcs:
        if str(src).endswith('.c'):
            srcsfile.write("CSRC += {}\n".format(src))
        elif str(src).endswith('.s'):
            srcsfile.write("ASSRC += {}\n".format(src))

    srcsfile.write('\n')

    for inc in mod.incs:
        srcsfile.write("INCS += -I{}\n".format(inc))
        includes.append(inc)

    srcsfile.write('\n')

    if mod.flags:
        for src in mod.srcs:
            objs = str(src).replace('.c', '.o').replace('.s', '.o')
            srcsfile.write("{} : CFLAGS = {}\n".format(
                projSettings['FOLDER_OUT'] / str(objs), plib.compilerOptsByModuleToLine(mod.flags)))

    srcsfile.write('\n')

srcsfile.close()

strIncs = []
aux = []

if compilerSettings['INCLUDES']:
    aux += compilerSettings['INCLUDES']
if includes:
    aux += includes

strIncs = [str(i) for i in aux]

listToExclude = []

if (USE_EXCLUDE_FOLDERS):
    
    allIncFoldes = []
    includes = [str(i) for i in includes]

    for filename in Path('.').rglob('*.h'):
        allIncFoldes.append(str(filename.parent))

    allIncFoldes = list(dict.fromkeys(allIncFoldes))
    allIncFoldes.sort()

    filtedist = []
    parent = ""
    for p in allIncFoldes:
        if parent == "":
            parent = p
            filtedist.append(p)
        elif(p.startswith(parent+"/")):
            None
        else:
            parent = p
            filtedist.append(p)

    allIncFoldes = filtedist

    p = re.compile('^(I|i)nc(lude)*$')

    for allinc in allIncFoldes:
        aux = allinc + '/'
        if not any(aux.startswith(a + "/") for a in includes):
            if not str(allinc).startswith('Test/ceedling') and not allinc == '.':
                auxpath = Path(allinc)
                if p.match(auxpath.name):
                    listToExclude.append(str(auxpath.parent))
                else:
                    listToExclude.append(allinc)
            
    listToExclude.append('Test/ceedling')
    

cproject_setting = {
    'C_INCLUDES': strIncs,
    'C_SYMBOLS': compilerOpts['MACROS'],
    'C_EXCLUDE': listToExclude
}

cp.generate_cproject(cproject_setting)
