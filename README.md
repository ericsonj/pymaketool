# pymaketool
<p align=center>
<img src="https://img.shields.io/pypi/l/pymaketool.svg">
<img src="https://img.shields.io/pypi/wheel/pymaketool.svg">
<img src="https://img.shields.io/badge/python-%3E=_3.10-green.svg">
<img src="https://img.shields.io/github/v/tag/ericsonj/pymaketool">
<img src="https://github.com/ericsonj/pymaketool/actions/workflows/test.yml/badge.svg?branch=master">
</p>

**pymaketool** is an elegant and simple tool to build and manage large C/C++ projects and libraries.
The main purpose is to simplify the build process by using Python to find and organize source files.

```
my_project/
│
├── Makefile                    ← root entry point (calls pymaketool)
├── .env                        ← environment variables (optional, not committed)
│
├── pymake/                     ← build config folder
│   ├── Makefile.py             ← YOU write this  (toolchain, flags, targets)
│   ├── makefile.mk             ← generated
│   ├── vars.mk                 ← generated
│   ├── srcs.mk                 ← generated
│   └── targets.mk              ← generated
│
├── app/                        ← source module
│   ├── inc/
│   │   └── main.h
│   ├── src/
│   │   └── main.c
│   └── app_mk.py               ← YOU write this  (can be empty!)
│
├── utils/                      ← another source module
│   ├── utils.c
│   ├── utils.h
│   └── utils_mk.py             ← YOU write this  (module())
│
└── build/                      ← generated output
    ├── app                     ← final binary
    └── obj/
        ├── app/src/main.o
        └── utils/utils.o
```

## Quick Start

Install required packages:

### Ubuntu
```bash
$ sudo apt-get install -y gcc make python3 python3-pip git time zip
```

### Fedora
```bash
$ sudo dnf install python3 python3-pip time zip git gcc
```

### Arch Linux
```bash
$ sudo pacman -S gcc make python python-pip time zip git
```

Install pymaketool:
```bash
$ pip3 install pymaketool
```

Create and build a new C project:
```bash
$ pynewproject CLinuxGCC
  (author) Your name: Ericson
  (project_name) Your project name: hello

$ cd hello
hello$ make
hello$ ./build/hello
```

## Quick Start with Poetry

If you prefer [Poetry](https://python-poetry.org/) for dependency management:

```bash
$ curl -sSL https://install.python-poetry.org | python3 -

$ pynewproject CLinuxGCC
  (project_name) Your project name: hello

$ cd hello
hello$ poetry init --name hello --dependency pymaketool
hello$ poetry install
hello$ poetry run make
hello$ ./build/hello
```

## Quick start in Docker

```bash
$ docker pull ericsonjoseph/pymaketool
$ docker run -it ericsonjoseph/pymaketool
ubuntu@$ pynewproject CLinuxGCC
```

---

## Module Files (`*_mk.py` / `*.mk.py`)

**pymaketool** discovers all `*_mk.py` and `*.mk.py` files recursively in your project. Each file describes one source module (a directory of C/C++ files).

### Zero lines — empty file (simplest)

Leave the file completely empty. pymaketool auto-discovers all `.c` and `.h` files in the same directory:

```python
# app/app_mk.py  ← file can be completely empty
```

### One line — `module()`

```python
# app/app_mk.py
from pymakelib.pym import module
module()
```

With explicit file lists:

```python
from pymakelib.pym import module
module(srcs=['src/main.c', 'src/util.c'], incs=['inc/'])
```

### Class-based — full control

Use this when you need custom discovery logic, per-module compiler flags, or static libraries:

```python
# app/app_mk.py
from pymakelib import module

@module.ModuleClass
class App(module.BasicCModule):
    pass  # auto-discovers .c/.h in the module directory
```

Override methods for custom behaviour:

```python
@module.ModuleClass
class App(module.BasicCModule):

    def getSrcs(self) -> list:
        return self.getSrcsWithPath(['main.c', 'util.c'])

    def getIncs(self) -> list:
        return self.getIncsWithPath(['inc/'])

    def getCompilerOpts(self):
        from pymakelib import CompilerOpts
        opts = CompilerOpts()
        opts.warnings = ['-Wall', '-Werror']
        return opts.to_dict()
```

For C++ modules use `BasicCppModule` (auto-discovers `.cpp`/`.cc`/`.C` and `.h`/`.hpp`):

```python
from pymakelib import module

@module.ModuleClass
class Core(module.BasicCppModule):
    pass
```

### Static library module

```python
from pymakelib import module

@module.ModuleClass
class ExtLib(module.ExternalModule):

    def init(self):
        return module.StaticLibrary("modulelib", "Release", rebuild=True)

    def getModulePath(self) -> str:
        return '/LIBS/module_lib/module_lib_mk.py'
```

---

## Project Configuration (`Makefile.py`)

`Makefile.py` is the project entry point. It defines the toolchain, compiler flags, and build targets.

### New API — `ProjectConfig` (recommended)

```python
# pymake/Makefile.py
from pymakelib import ProjectConfig, Makeclass, CompilerOpts, MKVARS, Target
from pymakelib.toolchain import get_gcc_linux

@Makeclass
class Build(ProjectConfig):
    name         = 'myapp'
    output_dir   = 'build/obj/'
    compiler_set = get_gcc_linux()   # or get_gcc_arm_none_eabi('/opt/arm/bin/')

    def compiler_opts(self, opts: CompilerOpts) -> CompilerOpts:
        opts.optimize     = ['-O2']
        opts.debugging    = ['-g3']
        opts.warnings     = ['-Wall']
        opts.standard     = ['-std=c11']
        opts.preprocessor = ['-MP', '-MMD']
        opts.macros       = {'VERSION': '"1.0"'}
        return opts

    def targets(self):
        return {
            'TARGET': Target(
                file   = f'build/{self.name}',
                script = [MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS],
                logkey = 'OUT',
            ),
        }
```

**Multi-output builds** (ELF → HEX → BIN) — target dict order defines the dependency chain:

```python
    def targets(self):
        return {
            'TARGET':     Target(file='build/app.elf',
                                 script=[MKVARS.LD, '-o', '$@', MKVARS.OBJECTS, MKVARS.LDFLAGS],
                                 logkey='LINK'),
            'TARGET_HEX': Target(file='build/app.hex',
                                 script=['objcopy', '-O', 'ihex', MKVARS.TARGET, '$@'],
                                 logkey='HEX'),
            'TARGET_BIN': Target(file='build/app.bin',
                                 script=[MKVARS.OBJCOPY, '-O', 'binary', MKVARS.TARGET, '$@'],
                                 logkey='BIN'),
        }
```

**Phony targets** (flash, format, test…):

```python
    def getPhonyTargets(self):
        return {
            'flash': {
                'deps':   ['all'],
                'logkey': 'FLASH',
                'script': 'openocd -f board/board.cfg -c "program build/app.elf verify reset exit"',
            },
        }
```

**IDE addons** — declare as a list attribute instead of a module-level call:

```python
from pymakelib.eclipse_addon import EclipseAddon
from pymakelib.vscode_addon import VSCodeAddon

@Makeclass
class Build(ProjectConfig):
    addons       = [EclipseAddon, VSCodeAddon]
    compiler_set = get_gcc_linux()
    ...
```

**Linker options**:

```python
    def linker_opts(self, opts: LinkerOpts) -> LinkerOpts:
        opts.script  = ['-T', 'link.ld']
        opts.machine = ['-mthumb', '-mcpu=cortex-m4']
        opts.libs    = ['-lm', '-lc']
        return opts
```

### Environment variables (`.env` support)

```python
# pymake/Makefile.py
from pymakelib import ProjectConfig, Makeclass, resolve_env
from pymakelib.toolchain import get_gcc_arm_none_eabi

@Makeclass
class Build(ProjectConfig):
    env_file     = '.env'   # loaded automatically before any get* call
    compiler_set = get_gcc_arm_none_eabi(resolve_env('XC32_PATH', '/opt/xc32/bin/'))
    ...
```

`.env` file (not committed to version control):
```
XC32_PATH=/opt/microchip/xc32/v4.60/bin
PROGRAMMER=PK5
```

`load_dotenv()` and `resolve_env()` are also available for module-level use:

```python
from pymakelib import load_dotenv, resolve_env

load_dotenv()
TOOLCHAIN = resolve_env('TOOLCHAIN_PATH', '/usr/bin/')
```

### Toolchain presets

| Function | Description |
|----------|-------------|
| `get_gcc_linux()` | Host Linux GCC |
| `get_gpp_linux()` | Host Linux G++ (C++) |
| `get_gcc_arm_none_eabi()` | ARM bare-metal cross-compiler |

All return a `CompilerSet` dataclass with IDE autocompletion for every tool path.

---

## Typed Configuration Reference

All new configuration types live in `pymakelib` and provide IDE autocompletion.

### `CompilerOpts`

| Field | Makefile variable | Example |
|-------|------------------|---------|
| `macros` | `-D` defines | `{'DEBUG': None, 'VER': '"2.0"'}` |
| `machine` | machine/arch flags | `['-mthumb', '-mcpu=cortex-m4']` |
| `optimize` | optimisation | `['-O2']` |
| `debugging` | debug info | `['-g3']` |
| `preprocessor` | preprocessor | `['-MP', '-MMD']` |
| `warnings` | warnings | `['-Wall', '-Werror']` |
| `standard` | language std | `['-std=c11']` |
| `general` | other flags | `['--coverage']` |

### `Target`

```python
Target(
    file   = 'build/app.elf',           # output file path
    script = [MKVARS.LD, '-o', '$@',    # command tokens joined with spaces
               MKVARS.OBJECTS, MKVARS.LDFLAGS],
    logkey = 'LINK',                     # label shown in build output
)
```

`script` tokens are joined with a space into one Makefile recipe line. Use `&&` for shell chaining: `['@mkdir -p $(dir $@) &&', MKVARS.LD, ...]`.

---

For install guide go to [install-guide](docs/install/install-guide.md)

For more documentation go to [Read the Docs](https://pymaketool.readthedocs.io/en/latest/)