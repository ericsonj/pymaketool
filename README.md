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

📂 **my_project/**

<ul>
  <li>📄 Makefile <sub>← root entry point</sub></li>
  <li>📄 .env <sub>← environment variables (not committed)</sub></li>
  <li><details open><summary>📂 <b>pymake/</b> <sub>← build config folder</sub></summary>
    <ul>
      <li>📄 <b>Makefile.py</b> <sub>✏️ YOU write this · toolchain · flags · targets</sub></li>
      <li>📄 makefile.mk <sub>← generated</sub></li>
      <li>📄 vars.mk <sub>← generated</sub></li>
      <li>📄 srcs.mk <sub>← generated</sub></li>
      <li>📄 targets.mk <sub>← generated</sub></li>
    </ul>
  </details></li>
  <li><details open><summary>📂 <b>app/</b> <sub>← source module</sub></summary>
    <ul>
      <li><details><summary>📂 inc/</summary><ul><li>📄 main.h</li></ul></details></li>
      <li><details><summary>📂 src/</summary><ul><li>📄 main.c</li></ul></details></li>
      <li>🐍 <b>mk.py</b> <sub>✏️ YOU write this · recommended</sub>

```python
from pm import mk

mk(srcs=["src/main.c"], incs=["inc"])
```
```python
## Or just:
from pm import mk

mk()
```
```python
## Or nothing at all:

```

</li>
    </ul>
  </details></li>
  <li><details open><summary>📂 <b>utils/</b> <sub>← another source module</sub></summary>
    <ul>
      <li>📄 utils.c</li>
      <li>📄 utils.h</li>
      <li>🐍 <b>utils_mk.py</b> <sub>✏️ also supported</sub></li>
    </ul>
  </details></li>
  <li><details><summary>📂 <b>build/</b> <sub>← generated output</sub></summary>
    <ul>
      <li>⚙️ app <sub>← final binary</sub></li>
      <li><details><summary>📂 obj/</summary><ul><li>📄 app/src/main.o</li><li>📄 utils/utils.o</li></ul></details></li>
    </ul>
  </details></li>
</ul>

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

## Module Files (`mk.py`, `*_mk.py`, `*.mk.py`)

**pymaketool** discovers module files recursively. The shortest and recommended name is `mk.py`, but `app_mk.py` and `app.mk.py` still work.

Each module file describes one folder of C/C++ code.

### Recommended DX: `from pm import mk`

```python
# app/mk.py
from pm import mk

mk()
```

That is enough for most modules. `mk()` captures the current file path and auto-discovers sources and includes in the same directory.
If you want zero lines, an empty `mk.py` also works.

### Common cases

Explicit files:

```python
from pm import mk

mk(srcs=["src/main.c", "src/util.c"], incs=["inc"])
```

Exclude files from auto-discovery:

```python
from pm import mk, skip

mk(srcs=skip("test*", "mock_*"), incs=[".", "include"])
```

C++ module:

```python
from pm import mk

mk(lang="cpp")
```

### When to use the class API

Use the class-based API only when you need custom module behavior, static libraries, or full control over discovery.

```python
from pymakelib import module

@module.ModuleClass
class App(module.BasicCModule):
    pass
```

---

## Ignoring Modules During Discovery

**pymaketool** automatically reads `.gitignore` by default and applies gitignore-style pattern matching to skip module files during discovery. You can also use `.moduleignore` for pymaketool-specific ignore patterns.

### Quick start

Create a `.moduleignore` file in `pymake/` (or project root as fallback):

```gitignore
# Ignore test modules
tests/
*_test_mk.py

# Ignore vendor code
vendor/
third_party/

# Ignore specific modules
experimental/prototype_mk.py
```

### Pattern syntax

`.moduleignore` and `.gitignore` use **gitignore-style patterns**:

| Pattern | Matches |
|---------|---------|
| `test_*.py` | Any file starting with `test_` |
| `build/` | Entire `build/` directory and its contents |
| `**/temp_*` | `temp_*` files at any depth |
| `*.tmp` | Any file ending with `.tmp` |
| `!important_mk.py` | Negation: exclude `important_mk.py` from ignore |

Comments (`#`) and blank lines are ignored.

### Source precedence

Ignore patterns are merged from multiple sources in this order:

1. **`.gitignore`** (project root) — read by default
2. **`.moduleignore`** (`pymake/.moduleignore` preferred, fallback to root `.moduleignore`)
3. **`Makefile.py`** — additional patterns via `ignore_list`

Later sources can override earlier ones using negation (`!pattern`).

### Control via Makefile.py

Disable `.gitignore` or add extra patterns:

```python
from pymakelib import ProjectConfig, Makeclass

@Makeclass
class Build(ProjectConfig):
    use_gitignore = False               # disable .gitignore reading
    ignore_list   = ['vendor/', 'tmp/'] # additional patterns
    ...
```

Or override the `getIgnoreConfig()` method for dynamic control:

```python
@Makeclass
class Build(ProjectConfig):
    ...
    
    def getIgnoreConfig(self):
        return {
            'use_gitignore': True,
            'ignore_list': ['tests/', 'experimental/']
        }
```

### File location

- **Preferred**: `pymake/.moduleignore` (alongside `Makefile.py`)
- **Fallback**: `.moduleignore` in project root (for legacy projects)

**Why `.gitignore` by default?** Most projects already ignore build artifacts, vendor code, and tests in `.gitignore`. Reading it by default reduces duplication and follows the principle of least surprise.

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