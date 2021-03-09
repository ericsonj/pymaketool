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

from pymakelib import Define as D

def out(value):
    lines = value.splitlines()
    for l in lines:
        print(l)

def comment(value: str):
    lines = value.splitlines()
    out("/**")
    for l in lines:
        out(" * "+l.strip())
    out(" */")

def enum(names, values=[0]):
    resp = ''
    resp += "enum {\n"
    idx = 0
    for n in names:
        v = None
        try:
            v = values[idx]
        except:
            v = None
            pass
        if isinstance(v, int):
            resp += f"    {n} = {v},\n"
        else:
            resp += f"    {n},\n"
        idx += 1
    resp += "};"
    out(resp)


def enum_sf(strformat, range, init=0):
    values = []
    for r in range:
        values.append(strformat.format(r))
    enum(values, [init])

def enum_str_map(name, strdict: dict):
    keys = list(strdict.keys())
    enum(keys)
    out("""#define {0}_VALUES  =\\
    {{\\
{1}\\
    }}
    """.format(name.upper(),'\\\n'.join([ f"{' ':8}\"{strdict[n]}\"," for n in keys])))
    out("""
#ifndef DECL_{0}
#define _DECL extern
#define _VAR
#else
#define _DECL
#define _VAR  {0}_VALUES
#endif
    """.format(name.upper()))
    out("""
_DECL char* {0}[{1}] _VAR;
    """.format(name, len(keys)))

def __format_name(name:str) -> str:
    name = name.upper()
    name = name.replace('/', '_')
    name = name.replace('.', '_')
    if not name.startswith('_'):
        name = '_'+name
    if not name.endswith('_'):
        name = name + '_'
    return name 

def HEADER_FILE(*args, **kwargs):
    
    def inner(func):
        if 'name' in kwargs.keys():
            name =  kwargs['name']
        else:
            name = func.__name__
        name = __format_name(name)
        out(f"#ifndef {name}")
        out(f"#define {name}")
        func()
        out(f"#endif // {name}")
         
    # reurning inner function    
    return inner

