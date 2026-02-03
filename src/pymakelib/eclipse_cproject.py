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


# Generate .cproject from .cproject_template
#
# Wildcards:
#   <!--wildcard_c_includes-->      : C Includes
#   <!--wildcard_c_symbols-->       : C Symbols
#   <!--wildcard_cpp_includes-->    : C++ Includes
#   <!--wildcard_cpp_symbols-->     : C++ Symbols

# listconf = {'C_INCLUDES': [...], 'C_SYMBOLS' : [...], 'CPP_INCLUDES': [...], 'CPP_SYMBOLS': [...]}
from pathlib import Path
from . import preconts as K
from . import Define as D
import os.path
from os import path


CPROJECT_TEMPLATE = K.PYMAKEPROJ + '/.cproject_template'
CPROJECT = '.cproject'

LANGUAGE_SETTINGS_TEMPLATE = K.PYMAKEPROJ + '/.language.settings_template'
LANGUAGE_SETTINGS = '.settings/language.settings.xml'

LANGUAGE_SETTING_PROVIDER = """
                        <provider class="org.eclipse.cdt.managedbuilder.language.settings.providers.GCCBuiltinSpecsDetector" console="false" env-hash="-374963487674273350" id="org.eclipse.cdt.managedbuilder.core.GCCBuiltinSpecsDetector" keep-relative-paths="false" name="CDT GCC Built-in Compiler Settings" parameter="{0} -E -P -v -dD &quot;${{INPUTS}}&quot;" prefer-non-shared="true">
                                <language-scope id="org.eclipse.cdt.core.gcc"/>
                                <language-scope id="org.eclipse.cdt.core.g++"/>
                        </provider>
"""

WILDCARD_C_INCLUDES = '<!--wildcard_c_includes-->'
WILDCARD_C_SYMBOLS = '<!--wildcard_c_symbols-->'
WILDCARD_C_EXCLUDE = '<!--wildcard_c_exclude-->'

WILDCARD_LS_PROVIDER = '<!--wildcard_ls_provider-->'

def generate_cproject(listconf: dict):
    print('Generate .cproject')
    try:
        cproject_template = open(CPROJECT_TEMPLATE, 'r')
        cproject = open(CPROJECT, 'w')

        for line in cproject_template:
            if(line.strip() == WILDCARD_C_INCLUDES):
                if listconf['C_INCLUDES']:
                    cproject.write((writeXmlIncludes(listconf['C_INCLUDES'])))
            if(line.strip() == WILDCARD_C_SYMBOLS):
                if listconf['C_SYMBOLS']:
                    cproject.write((writeXmlSymbols(listconf['C_SYMBOLS'])))
            if(line.strip() == WILDCARD_C_EXCLUDE):
                if listconf['C_EXCLUDE']:
                    cproject.write(writeXmlExcluding(listconf['C_EXCLUDE']))    
            else:
                cproject.write(line)

    except IOError:
        print('Files .cproject or .cproject_template no accessible')
    finally:
        cproject_template.close()
        cproject.close()

def generate_languageSettings(compilerSettings: dict):
    print('Generate .setting/language.settings.xml')
    try:
        try:
            if not (path.exists(K.ECLIPSE_SETTING)):
                os.mkdir(K.ECLIPSE_SETTING)
        except Exception as e:
            print(e)
            
        langsett_template = open(LANGUAGE_SETTINGS_TEMPLATE, 'r')
        langsett = open(LANGUAGE_SETTINGS, 'w')

        for line in langsett_template:
            if(line.strip() == WILDCARD_LS_PROVIDER):
                langsett.write(LANGUAGE_SETTING_PROVIDER.format(compilerSettings['CC']))
            else:
                langsett.write(line)

    except IOError:
        print('Files .cproject or .cproject_template no accessible')
    finally:
        langsett_template.close()
        langsett.close()


def writeXmlIncludes(incList):
    directory = Path("./srcs.mk")
    directory = str(directory.absolute().parent.name)
    w = []
    for i in incList:
        if str(i).startswith('/'):  # absolute path
            w.append("<listOptionValue builtIn=\"false\" value=\"" +
                     str(i) + "\"/>\n")
        else:  # realative path
            w.append(
                "<listOptionValue builtIn=\"false\" value=\"&quot;${workspace_loc:/"+directory+"/"+str(i)+"}&quot;\"/>\n")

    return ''.join(w)


def writeXmlExcluding(excList):
    w = [] 
    excludes = '|'.join(excList)
    w.append("<entry excluding=\"" + excludes + "\" flags=\"VALUE_WORKSPACE_PATH\" kind=\"sourcePath\" name=\"\"/>\n")
    return ''.join(w)

def writeXmlSymbols(symList):
    w = []
    
    if isinstance(symList, dict):
        for key in symList:
            if symList[key] != None and symList[key] != '':
                if isinstance(symList[key], str):
                    w.append('<listOptionValue builtIn=\"false\" value=\"{}=&quot;{}&quot;\"/>\n'.format(key, symList[key]))
                elif isinstance(symList[key], bool):
                    w.append('<listOptionValue builtIn=\"false\" value=\"{}={}\"/>\n'.format(key, '1' if symList[key] else '0'))
                elif isinstance(symList[key],D):
                    w.append('<listOptionValue builtIn=\"false\" value=\"{}={}\"/>\n'.format(key, symList[key].getDefine()))
                else:
                    w.append('<listOptionValue builtIn=\"false\" value=\"{}={}\"/>\n'.format(key, symList[key]))
            else:
                w.append('<listOptionValue builtIn=\"false\" value=\"{}\"/>\n'.format(key))
    else:
        for sym in symList:
            sym = str(sym).replace("\\\"", "&quot;")
            w.append("<listOptionValue builtIn=\"false\" value=\""+sym+"\"/>\n")

    return ''.join(w)
