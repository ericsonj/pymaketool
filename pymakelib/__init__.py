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
from .Log import getLogger

log = getLogger(__name__)

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
    STATIC_LIBS = '$(addprefix -L,$(dir $(SLIBS_OBJECTS))) $(addprefix -l,$(SLIBS_NAMES))'

def MOD_PATH(wk):
    return wk['modPath']

# Direct define  __USE_FILE__: D(file.h) => -D__USE_FILE__=file.h
class D:
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

class IProject(ABC):
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

def Makeclass(clazz):
    obj = clazz()
    if not isinstance(obj, IProject):
        log.warning(f"class \'{clazz.__name__}\' in Makefile.py not inheritance of pymakelib.IProject")
    global ProjectInstance
    ProjectInstance = obj


def getProjectInstance() -> IProject:
    try:
        _ = ProjectInstance
        return ProjectInstance
    except NameError:
        log.debug("not Makeclass mode")
        pass
    return None

