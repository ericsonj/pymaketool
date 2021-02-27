from . import Project

def out(value):
    print(value)

def comment(value: str):
    lines = value.splitlines()
    out("/**")
    for l in lines:
        out(" * "+l.strip())
    out(" */")

def defined(key):
    sett = Project.getSettings()
    macros = sett['COMPILER_OTPS']['MACROS']
    if key in macros:
       return macros[key] 

def enum(names, values):
    resp = ''
    resp += "enum {\n"
    idx = 0
    for n in names:
        v = None
        try:
            v = values[idx]
        except:
            pass
        if v:
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


def cstrarray(name, values):
    resp = ''
    resp += f"const char* {name}[{len(values)}] = "+"{\n"
    for v in values:
        resp += f"    \"{v}\",\n"
    resp += "};"
    out(resp)


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

