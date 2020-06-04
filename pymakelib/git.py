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
from pathlib import Path
import subprocess
from . import moduleignore

def getCommitHash(abbreviated=True):
    hashValue = ''
    cmd = ['git', 'rev-parse', 'HEAD']
    try:
        hashValue = subprocess.check_output(cmd).strip().decode('utf-8')
        if hashValue:
            hashValue = hashValue[:7] if abbreviated else hashValue
    except:
        print('WARNING: Can not get commit hash')
        
    return hashValue


def getBranchName():
    branchName = ''
    try:
        branchName = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode('utf-8')
    except:
        print('WARNING: Can not get commit hash')

    return branchName


def getDescribe(options='--long'):
    desc = ''
    try:
        desc = subprocess.check_output(['git','describe', options]).strip().decode('utf-8')
    except:
        print('WARNING: Can not get commit hash')
        
    return desc


def printRelativePath(filemacro):
    print(os.path.dirname(os.path.abspath(filemacro)))


@DeprecationWarning
def addSubmodule(url, dst_dir, isPyMakeModule=False, exclModulesPaths=[]):
    dstDir = Path(Path(dst_dir) / '.git')
    if dstDir.exists():
        moduleignore.writeIgnoreFile(exclModulesPaths)
        return

    cmd1 = ['git',  'submodule', 'add', url, dst_dir]
    cmd2 = ['git',  'submodule', 'init']
    cmd3 = ['git',  'submodule', 'update']
    
    try:
        subprocess.check_output(cmd1).strip().decode('utf-8')
    except:
        pass

    try:
        subprocess.check_output(cmd2).strip().decode('utf-8')
    except:
        pass

    try:
        subprocess.check_output(cmd3).strip().decode('utf-8')
    except:
        pass

    if isPyMakeModule:
        moduleignore.writeIgnoreFile(exclModulesPaths)
