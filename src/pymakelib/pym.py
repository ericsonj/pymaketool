"""pym.py — functional API for declaring pymaketool modules without a class.

Instead of:
    from pymakelib import module as _mod
    @_mod.ModuleClass
    class App(_mod.BasicCModule):
        pass

Write:
    from pymakelib.pym import module
    module()

Or leave the file completely empty — pymaketool will auto-discover sources.
"""

from fnmatch import fnmatch
from pathlib import Path
from typing import List, Optional, TypedDict, Union
import sys

from pymakelib import module as _module
from pymakelib.module import SrcType, IncType


class ExcludeFilter(TypedDict):
    """Dict shape accepted by ``mk(srcs=...)`` and ``mk(incs=...)`` for auto-discover with exclude.

    Use ``skip(...)`` as a shorthand to create this dict.
    """
    exclude: List[str]


SrcsArg = Union[List[str], ExcludeFilter, None]
"""Type for the ``srcs`` parameter: explicit list, exclude filter, or None (auto-discover)."""

IncsArg = Union[List[str], ExcludeFilter, None]
"""Type for the ``incs`` parameter: explicit list, exclude filter, or None (auto-discover)."""


_LANG_SRC_TYPE = {
    "c": SrcType.C_AND_ASM,
    "cpp": SrcType.CPP_AND_ASM,
    "c++": SrcType.CPP_AND_ASM,
}

_LANG_INC_TYPE = {
    "c": IncType.C,
    "cpp": IncType.CPP,
    "c++": IncType.CPP,
}


def skip(*patterns: str) -> ExcludeFilter:
    """Create an exclude-filter dict for use with ``mk(srcs=...)`` or ``mk(incs=...)``.

    Returns a dict ``{"exclude": [...]}``. When ``mk()`` receives this instead
    of a plain list, it auto-discovers sources/includes and filters out any
    file or directory whose name matches one of the fnmatch patterns.

    Args:
        *patterns: Fnmatch patterns for files/directories to skip.

    Returns:
        ExcludeFilter: ``{"exclude": list[str]}``

    Examples::

        from pm import mk, skip

        mk(srcs=skip("test*", ".template"))
        # equivalent to:
        mk(srcs={"exclude": ["test*", ".template"]})
    """
    return {"exclude": list(patterns)}


def __getmodule_caller(func):
    def stack_(frame):
        framelist = []
        while frame:
            framelist.append(frame)
            frame = frame.f_back
        return framelist

    stack_list = stack_(sys._getframe(1))
    idx = 0
    for stack in stack_list:
        idx += 1
        if stack.f_code.co_name == func:
            break
    parentframe = stack_list[idx]
    return parentframe.f_code.co_filename


def _register_module(caller_file, srcs=None, incs=None, compiler_opts=None, base_class=None):
    """Internal: register a module with an already-resolved caller file path.

    This is the core implementation used by both module() and the mk package.
    Separating caller detection from registration allows external callers to
    capture their own stack frame before delegating here.

    Args:
        base_class: Module base class (BasicCModule or BasicCppModule).
                    Defaults to BasicCModule if None.
    """
    if base_class is None:
        base_class = _module.BasicCModule

    @_module.ModuleClass
    class _SimpleModule(base_class):

        # pylint: disable=no-self-argument
        def get_path(_self):
            return caller_file

        def getSrcs(_self):
            if srcs is not None:
                return _self.srcs_from(srcs)
            return super().getSrcs()

        def getIncs(_self):
            if incs is not None:
                return _self.incs_from(incs)
            return super().getIncs()

        def getCompilerOpts(_self):
            if compiler_opts is None:
                return None
            if hasattr(compiler_opts, "to_dict"):
                return compiler_opts.to_dict()
            return compiler_opts


def module(srcs=None, incs=None, compiler_opts=None):
    """Declare a C module in one line without writing a class.

    Registers a BasicCModule for the directory containing the calling file.
    When arguments are None, auto-discovers sources/includes (same as BasicCModule).

    Args:
        srcs:          list of source filenames relative to the module dir,
                       or None for auto-discover all .c files (default)
        incs:          list of include dirs relative to the module dir,
                       or None for auto-discover (default: module dir itself)
        compiler_opts: CompilerOpts instance or raw dict with per-module flags,
                       or None for no extra flags (default)

    Examples:
        # Auto-discover everything (equivalent to empty file):
        from pymakelib.pym import module
        module()

        # Explicit sources:
        module(srcs=['src/main.c', 'src/util.c'], incs=['inc/'])

        # With per-module flags:
        from pymakelib import CompilerOpts
        opts = CompilerOpts()
        opts.warnings = ['-Wall', '-Werror']
        module(compiler_opts=opts)
    """
    caller_file = __getmodule_caller("module")
    _register_module(caller_file, srcs, incs, compiler_opts)


simple_module = module


def add_library(name, outputdir, srcs=[], incs=[]):

    @_module.ModuleClass
    class _(_module.BasicCModule, _module.StaticLibraryModule):

        def get_module_name(self):  #
            return str(name).capitalize()  #
            # Not need in class mode

        def get_path(self):  #
            return __getmodule_caller("add_library")  #

        def get_lib_name(self) -> str:
            return name

        def get_lib_outputdir(self) -> str:
            return outputdir

        def getSrcs(self):
            return super().getSrcs() if not srcs else srcs

        def getIncs(self):
            return super().getIncs() if not incs else incs


# ---------------------------------------------------------------------------
# Source/Include discovery helpers with exclude patterns
# ---------------------------------------------------------------------------


def _resolve_srcs(srcs: SrcsArg, module_dir: Path, lang: str = "c") -> Optional[List[str]]:
    """Resolve srcs argument: list passes through, dict triggers discovery with exclude."""
    if srcs is None:
        return None
    if isinstance(srcs, list):
        return srcs
    if isinstance(srcs, dict):
        exclude = srcs.get("exclude", [])
        src_type = _LANG_SRC_TYPE.get(lang, SrcType.C_AND_ASM)
        return _discover_sources(module_dir, src_type, exclude)
    raise TypeError(f"srcs must be a list, dict, or None — got {type(srcs).__name__}")


def _resolve_incs(incs: IncsArg, module_dir: Path, lang: str = "c") -> Optional[List[str]]:
    """Resolve incs argument: list passes through, dict triggers discovery with exclude."""
    if incs is None:
        return None
    if isinstance(incs, list):
        return incs
    if isinstance(incs, dict):
        exclude = incs.get("exclude", [])
        inc_type = _LANG_INC_TYPE.get(lang, IncType.C)
        return _discover_includes(module_dir, inc_type, exclude)
    raise TypeError(f"incs must be a list, dict, or None — got {type(incs).__name__}")


def _matches_any_pattern(path: Path, patterns: List[str]) -> bool:
    """Check if any part of the path matches any fnmatch pattern.

    Checks both the filename and each directory component in the path.
    """
    name = path.name
    parts = path.parts

    for pattern in patterns:
        # Check filename
        if fnmatch(name, pattern):
            return True
        # Check each directory component
        for part in parts[:-1]:  # exclude filename, already checked
            if fnmatch(part, pattern):
                return True
    return False


def _discover_sources(
    module_dir: Path,
    src_type: List[str],
    exclude: Optional[List[str]] = None,
) -> List[str]:
    """Internal: discover sources in module_dir with exclude filtering.

    Returns filenames relative to module_dir (not project root).
    """
    exclude = exclude or []
    sources = []

    for ext in src_type:
        for src_path in module_dir.rglob("*" + ext):
            rel_path = src_path.relative_to(module_dir)
            if exclude and _matches_any_pattern(rel_path, exclude):
                continue
            sources.append(str(rel_path))

    return sorted(sources)


def _discover_includes(
    module_dir: Path,
    inc_type: List[str],
    exclude: Optional[List[str]] = None,
) -> List[str]:
    """Internal: discover include directories in module_dir with exclude filtering.

    Returns directory paths relative to module_dir.
    """
    exclude = exclude or []
    inc_dirs = set()

    for ext in inc_type:
        for header_path in module_dir.rglob("*" + ext):
            rel_path = header_path.relative_to(module_dir)
            if exclude and _matches_any_pattern(rel_path, exclude):
                continue
            # Add parent directory of header
            parent = rel_path.parent
            inc_dirs.add(str(parent) if str(parent) != "." else ".")

    return sorted(inc_dirs) if inc_dirs else ["."]


def find_srcs(
    exclude: Optional[List[str]] = None,
    ext: Optional[List[str]] = None,
) -> List[str]:
    """Discover source files with optional exclude patterns.

    Call this from a module file (``*_mk.py``) to auto-discover sources
    in that module's directory, filtering out files/directories that match
    any of the exclude patterns.

    Args:
        exclude: Fnmatch patterns for files/directories to skip.
            Patterns are matched against filenames AND directory names.
            Examples: ``["test*", "*.template*", "mock_*"]``
        ext: File extensions to search for. Defaults to
            :attr:`SrcType.C_AND_ASM` (``.c``, ``.s``, ``.S``, ``.asm``).
            Use :attr:`SrcType.CPP_AND_ASM` for C++ projects,
            or pass custom extensions like ``[".c", ".cpp"]``.

    Returns:
        List of source filenames relative to the module directory,
        ready to pass to ``mk(srcs=...)``.

    Examples:
        Auto-discover C sources, excluding test directories::

            from pm import mk, find_srcs
            mk(srcs=find_srcs(exclude=["test*", "mock_*"]))

        Discover only .c files (no assembly)::

            from pm import mk, find_srcs
            mk(srcs=find_srcs(ext=[".c"]))
    """
    # pylint: disable=protected-access
    caller_file = Path(sys._getframe(1).f_code.co_filename)
    module_dir = caller_file.parent

    if ext is None:
        ext = SrcType.C_AND_ASM

    return _discover_sources(module_dir, ext, exclude)


def find_incs(
    exclude: Optional[List[str]] = None,
    inc_type: Optional[List[str]] = None,
) -> List[str]:
    """Discover include directories with optional exclude patterns.

    Call this from a module file (``*_mk.py``) to auto-discover include
    directories (directories containing header files) in that module's
    directory, filtering out paths that match any exclude patterns.

    Args:
        exclude: Fnmatch patterns for files/directories to skip.
            Patterns are matched against filenames AND directory names.
            Examples: ``["test*", "internal/*"]``
        inc_type: Header extensions to search for. Defaults to
            :attr:`IncType.C` (``.h``). Use :attr:`IncType.CPP` for
            C++ headers (``.h``, ``.hpp``, etc.).

    Returns:
        List of include directory paths relative to the module directory,
        ready to pass to ``mk(incs=...)``.

    Examples:
        Auto-discover include dirs, excluding test headers::

            from pm import mk, find_srcs, find_incs
            mk(
                srcs=find_srcs(exclude=["test*"]),
                incs=find_incs(exclude=["test*"]),
            )
    """
    # pylint: disable=protected-access
    caller_file = Path(sys._getframe(1).f_code.co_filename)
    module_dir = caller_file.parent

    if inc_type is None:
        inc_type = IncType.C

    return _discover_includes(module_dir, inc_type, exclude)
