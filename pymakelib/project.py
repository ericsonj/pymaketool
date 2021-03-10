# Copyright (c) 2021, Ericson Joseph
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

from pymakelib import Pymaketool
from pymakelib import Logger
from pymakelib.module import CompilerOptions
from pymakelib import Define

log = Logger.getLogger()

def setSettings(settings):
    global __settings
    try:
        _ = __settings
    except NameError:
        log.debug(f"create global modules list")
        __settings = settings


def getSettings():
    auxsetts = None
    try:
        _ = __settings
        return __settings
    except NameError:
        log.debug("not project settings found")
        p = Pymaketool()
        globalSettings = {
            'PROJECT_SETTINGS':  p.projSettings,
            'COMPILER_OTPS':     p.compilerOpts,
            'COMPILER_SETTINGS': p.compilerSettings
        }
        setSettings(globalSettings)
        auxsetts = __settings
        pass
    return auxsetts

def isdefined(key) -> bool:
    """Check if project have define.

    Args:
        key (str or D): name of define or macro

    Returns:
        bool: True if key is defined
    """
    sett = getSettings()
    macros = sett['COMPILER_OTPS']['MACROS']
    return (key in macros)


def define(key) -> str:
    """Get value of define if exist.

    Args:
        key (str): name of define (macro)

    Returns:
        str: value of define in string, if define value is None return '',if key is not defined return None
    """    
    sett = getSettings()
    macros = sett['COMPILER_OTPS']['MACROS']
    if isdefined(key):
        value = macros[key]
        return '' if not value else str(value)
    else:
        return None


def getCompilerOpts() ->  dict:
    """Get the project compiler options

    Returns:
        dict: General project compiler options
    """
    return getSettings()['COMPILER_OTPS']
