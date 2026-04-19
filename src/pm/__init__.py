"""pm — short functional API for pymaketool module declaration.

Usage:
    from pm import mk
    mk(incs=["MPLAB/PIC32MK"])

    # Or with other imports
    from pm import mk, BasicCModule, ModuleClass

The mk() function is equivalent to `from pymakelib.pym import module; module(...)`.
"""

import sys
from pathlib import Path
from typing import Literal

# Re-export functional API from pym
from pymakelib.pym import (
    _register_module,
    _resolve_srcs,
    _resolve_incs,
    add_library,
    simple_module,
    find_srcs,
    find_incs,
    skip,
    ExcludeFilter,
    SrcsArg,
    IncsArg,
)

# Re-export class-based API from pymakelib.module
from pymakelib.module import (
    AbstractModule,
    BasicCModule,
    BasicCppModule,
    ModuleClass,
    StaticLibraryModule,
    ExternalModule,
    POJOModule,
    SrcType,
    IncType,
)


_LANG_MAP = {
    "c": BasicCModule,
    "cpp": BasicCppModule,
    "c++": BasicCppModule,
}


def mk(
    srcs: SrcsArg = None,
    incs: IncsArg = None,
    compiler_opts=None,
    lang: Literal["c", "cpp", "c++"] = "c",
):
    """Declare a C/C++ module in one line.

    Captures the caller's file path and registers a module for it.
    When arguments are None, auto-discovers sources/includes.

    Args:
        srcs: Sources to compile. Accepts three forms:

            - ``None`` — auto-discover all sources (default).
            - ``list[str]`` — explicit filenames relative to the module dir.
            - ``ExcludeFilter`` — auto-discover minus excluded patterns.
              Use ``skip(...)`` or ``{"exclude": [...]}`` dict form.

        incs: Include directories. Accepts three forms:

            - ``None`` — auto-discover (default: module dir itself).
            - ``list[str]`` — explicit dirs relative to the module dir.
            - ``ExcludeFilter`` — auto-discover minus excluded patterns.
              Use ``skip(...)`` or ``{"exclude": [...]}`` dict form.

        compiler_opts: Per-module compiler flags. Accepts:

            - ``None`` — no extra flags (default).
            - ``CompilerOpts`` instance (calls ``.to_dict()`` internally).
            - Raw ``dict`` with compiler option keys.

        lang: Language for source discovery: ``"c"`` (default), ``"cpp"``,
            or ``"c++"``. Controls which file extensions are searched when
            using ``skip()`` or ``ExcludeFilter``.

    Examples::

        from pm import mk, skip

        # Auto-discover all C sources:
        mk()

        # Exclude patterns — skip() shorthand:
        mk(srcs=skip("test*", ".template"))

        # Exclude patterns — dict form:
        mk(srcs={"exclude": ["test*"]}, incs=[".", "inc"])

        # C++ module with excludes:
        mk(srcs=skip("test*"), lang="cpp")

        # Explicit sources:
        mk(srcs=["main.c", "util.c"])

        # Mix: auto-discover srcs with exclude, explicit incs:
        mk(srcs=skip("test*", "mock_*"), incs=[".", "include"])
    """
    base_class = _LANG_MAP.get(lang.lower())
    if base_class is None:
        raise ValueError(f"Unknown lang {lang!r}. Use 'c', 'cpp', or 'c++'.")
    # pylint: disable=protected-access
    caller_file = sys._getframe(1).f_code.co_filename
    module_dir = Path(caller_file).parent

    srcs = _resolve_srcs(srcs, module_dir, lang.lower())
    incs = _resolve_incs(incs, module_dir, lang.lower())

    _register_module(caller_file, srcs, incs, compiler_opts, base_class=base_class)


__all__ = [
    # Functional API
    "mk",
    "add_library",
    "simple_module",
    "find_srcs",
    "find_incs",
    "skip",
    "ExcludeFilter",
    "SrcsArg",
    "IncsArg",
    # Class-based API
    "AbstractModule",
    "BasicCModule",
    "BasicCppModule",
    "ModuleClass",
    "StaticLibraryModule",
    "ExternalModule",
    "POJOModule",
    "SrcType",
    "IncType",
]
