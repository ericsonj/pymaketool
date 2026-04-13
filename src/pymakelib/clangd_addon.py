from .addon import AddonAbstract
from pathlib import Path
from pymakelib import Define

import json


# ---------------------------------------------------------------------------
# Module-level helpers (pure functions — easily unit-tested)
# ---------------------------------------------------------------------------

_C_EXTENSIONS = {".c"}
_CXX_EXTENSIONS = {".cpp", ".cc", ".cxx"}
_ASM_EXTENSIONS = {".s", ".S", ".asm"}
_ALL_EXTENSIONS = _C_EXTENSIONS | _CXX_EXTENSIONS | _ASM_EXTENSIONS

# Keys in compilerOpts that are NOT flag lists
_NON_FLAG_KEYS = {"MACROS", "TARGETS"}


def _build_flags(compiler_opts: dict) -> list:
    """Flatten all list values from the compiler opts dict into a single flag list.

    Keys listed in _NON_FLAG_KEYS are skipped (MACROS produces -D flags
    separately; TARGETS is a build recipe, not a compiler flag).
    """
    flags = []
    if not isinstance(compiler_opts, dict):
        return flags
    for key, value in compiler_opts.items():
        if key in _NON_FLAG_KEYS:
            continue
        if isinstance(value, list):
            flags.extend(value)
        elif isinstance(value, str) and value:
            flags.append(value)
    return flags


def _filter_flags(flags: list, strip: list, strip_with_value: list = None) -> list:
    """Remove flags whose prefix matches any entry in *strip* or *strip_with_value*.

    * ``strip`` — standalone flags: only the matching token is removed.
      Examples: ``-MP``, ``-MMD``, ``-fframe-base-loclist``.
    * ``strip_with_value`` — flags that take the **next token** as their value
      when written without ``=`` (e.g. ``-mprocessor PIC32MX``).  Both the
      flag token and the following token are dropped.  When the value is
      embedded (``-mprocessor=PIC32MX``) the flag is still matched by prefix
      and only the single token is removed.
    """
    if strip_with_value is None:
        strip_with_value = []

    if not strip and not strip_with_value:
        return list(flags)

    result = []
    skip_next = False
    for flag in flags:
        if skip_next:
            skip_next = False
            continue
        matched = False
        for bad in strip_with_value:
            if flag.startswith(bad):
                matched = True
                # Space-separated form: ``-mprocessor PIC32MX`` — drop next token.
                if flag == bad:
                    skip_next = True
                break
        if not matched:
            for bad in strip:
                if flag.startswith(bad):
                    matched = True
                    break
        if not matched:
            result.append(flag)
    return result


def _macros_to_args(symbols: dict) -> list:
    """Convert a macros dict to a list of ``-D`` compiler arguments.

    Unlike ``generator.macrosDictToString`` this function does NOT add
    Makefile-escaping (``\\\"``); the result is suitable for the
    ``arguments`` array in ``compile_commands.json``.
    """
    args = []
    if not isinstance(symbols, dict):
        return args
    for name, value in symbols.items():
        if value is None or value == "":
            args.append(f"-D{name}")
        elif isinstance(value, bool):
            args.append(f"-D{name}={'1' if value else '0'}")
        elif isinstance(value, Define):
            raw = value.getDefine()
            args.append(f"-D{name}={raw}" if raw else f"-D{name}")
        else:
            args.append(f"-D{name}={value}")
    return args


# ---------------------------------------------------------------------------
# Addon class
# ---------------------------------------------------------------------------

class CompileCommandsAddon(AddonAbstract):
    """Generates ``compile_commands.json`` for clangd / VS Code IntelliSense.

    Output path: ``<config_dir>/compile_commands.json`` (typically
    ``pymake/compile_commands.json`` relative to the project root).

    Usage in ``Makefile.py``::

        from pymakelib.clangd_addon import CompileCommandsAddon
        from pymakelib import addon

        # Standalone flags to strip (no following argument):
        CompileCommandsAddon.strip_flags = ["-MP", "-MMD", "-fframe-base-loclist"]
        # Flags that consume the NEXT token as their value (-FLAG value form):
        CompileCommandsAddon.strip_flags_with_value = ["-mprocessor", "-mdfp", "-mreserve"]
        addon.add(CompileCommandsAddon)

    Then add to ``.vscode/settings.json``::

        { "clangd.arguments": ["--compile-commands-dir=pymake"] }
    """

    # Class-level attributes: users override before calling addon.add()
    strip_flags: list = []
    strip_flags_with_value: list = []

    def init(self):
        proj = self.projectSettings
        comp = self.compilerSettings

        config_dir = Path(proj["C_CONFIG_DIR"])
        out_file = config_dir / "compile_commands.json"
        project_root = Path(".").resolve()

        # --- Build the base argument components ---
        compiler_opts = proj.get("C_COMPILER_OPTS", {})
        raw_flags = _build_flags(compiler_opts)
        clean_flags = _filter_flags(
            raw_flags,
            self.__class__.strip_flags,
            self.__class__.strip_flags_with_value,
        )
        defines = _macros_to_args(proj.get("C_SYMBOLS", {}))
        includes = [f"-I{inc}" for inc in proj.get("C_INCLUDES", [])]

        cc = comp.get("CC", "cc")
        cxx = comp.get("CXX", cc)  # fall back to CC when CXX is absent

        entries = []
        for src_str in proj.get("C_SRCS", []):
            src_path = Path(src_str)
            suffix = src_path.suffix.lower()

            if suffix not in _ALL_EXTENSIONS:
                continue

            abs_file = (project_root / src_path).resolve()

            if suffix in _CXX_EXTENSIONS:
                compiler = cxx
            else:
                compiler = cc

            arguments = [compiler] + clean_flags + defines + includes + ["-c", str(abs_file)]

            entries.append({
                "directory": str(project_root),
                "file": str(abs_file),
                "arguments": arguments,
            })

        out_file.write_text(json.dumps(entries, indent=2))
        print(f"Generate {out_file} ({len(entries)} files)")
