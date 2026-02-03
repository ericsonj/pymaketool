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

PYMAKEPROJ  = '.pymakeproj'
MAKEFILE_PY = 'Makefile.py'
VARS_MK     = 'vars.mk'
TARGETS_MK  = 'targets.mk'
ECLIPSE_SETTING = '.settings'

MODULEIGNORE_FILE   = '.moduleignore'

MOD_WORKSPACE       = 'modPath'
MOD_COMPILER_OPTS   = 'compilerOpts'


MOD_F_INIT              = 'init'
MOD_F_GETSRCS           = 'getSrcs'
MOD_F_GETINCS           = 'getIncs'
MOD_F_GETCOMPILEROPTS   = 'getCompilerOpts'


MK_F_GETPROJECTSETTINGS = 'getProjectSettings'
MK_F_GETCOMPILERSET     = 'getCompilerSet'
MK_F_GETCOMPILEROPTS    = 'getCompilerOpts'
MK_F_GETLINKEROPTS      = 'getLinkerOpts'
MK_F_GETTARGETSSCRIPT   = 'getTargetsScript'


PROJSETT_PROJECTNAME    = 'PROJECT_NAME'
PROJSETT_FOLDEROUT      = 'FOLDER_OUT'


COMPILERSET_CC          = 'CC'
COMPILERSET_CXX         = 'CXX'
COMPILERSET_LD          = 'LD'
COMPILERSET_AR          = 'AR'
COMPILERSET_AS          = 'AS'
COMPILERSET_OBJCOPY     = 'OBJCOPY'
COMPILERSET_SIZE        = 'SIZE'
COMPILERSET_OBJDUMP     = 'OBJDUMP'
COMPILERSET_NM          = 'NM'
COMPILERSET_RANLIB      = 'RANLIB'
COMPILERSET_STRINGS     = 'STRINGS'
COMPILERSET_STRIP       = 'STRIP'
COMPILERSET_CXXFILT     = 'CXXFILT'
COMPILERSET_ADDR2LINE   = 'ADDR2LINE'
COMPILERSET_READELF     = 'READELF'
COMPILERSET_ELFEDIT     = 'ELFEDIT'


MK_KEY_MACROS               = 'MACROS'
MK_KEY_MACHINE_OPTS         = 'MACHINE-OPTS'
MK_KEY_OPTIMIZE_OPTS        = 'OPTIMIZE-OPTS'
MK_KEY_OPTIONS              = 'OPTIONS'
MK_KEY_DEBUGGING_OPTS       = 'DEBUGGING-OPTS'
MK_KEY_PREPROCESSOR_OPTS    = 'PREPROCESSOR-OPTS'
MK_KEY_WARNINGS_OPTS        = 'WARNINGS-OPTS'
MK_KEY_CONTROL_C_OPTS       = 'CONTROL-C-OPTS'
MK_KEY_GENERAL_OPTS         = 'GENERAL-OPTS'

COMPOPTS_MACROS_KEY = 'MACROS'
