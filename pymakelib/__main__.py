import sys
from . import Pymaketool
from . import generator
from . import prelib

from ninja_syntax import Writer

p = Pymaketool()

compSetting = p.compilerSettings
compOpts = p.compilerOpts
print(p.compilerOpts)
print(p.compilerOpts['TARGETS'])

with open('vars.ninja', "w") as varsfile:
    n = Writer(varsfile)
    for key, value in compSetting.items():
        if key != 'INCLUDES':
            n.variable(key, value)

    cflags = []
    if isinstance(compOpts, dict):
        for key in compOpts:
            if key == 'TARGETS':
                continue
            if (key == 'MACROS' and isinstance(compOpts[key], dict)):
                cflags.append(prelib.macrosDictToString(compOpts[key]))
            else:
                cflags.append(' '.join(compOpts[key]))
    elif isinstance(compOpts, list):
        for item in compOpts:
            cflags.append(item)

    n.variable("CFLAGS", ' '.join(cflags))


with open("build.ninja", "w") as buildfile:
    n = Writer(buildfile)

    n.include("vars.ninja")
    n.newline()
    n.rule(name="compile", command="$CC $CFLAGS $INCS -c $in -o $out", description="CC $in")
    n.newline()
    n.build('main.o', "compile", "app/application/main.c")

modules = p.read_modules([sys.argv[1]])
for m in modules:
    g = generator.MakeGenerator(m, p)
    print(g.process())
