from pymakelib import D

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

