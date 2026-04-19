"""Backward-compatibility shim for the old pynewproject <GeneratorName> syntax."""

import sys
import warnings
from types import SimpleNamespace

# Maps old generator class names to new catalog template names.
_NAME_MAP: dict[str, str] = {
    "CLinuxGCC": "clinuxgcc",
}

_KNOWN_COMMANDS = {"list", "new", "update", "info", "doctor", "-h", "--help", "-v", "--version"}


def detect_legacy(argv: list[str], catalog: dict) -> bool:
    """Return True if *argv* looks like old-style usage (e.g. CLinuxGCC author=X)."""
    if not argv:
        return False
    first = argv[0]
    if first in _KNOWN_COMMANDS:
        return False

    # Match either a hardcoded name or anything in the catalog.
    from .catalog import find_template  # avoid circular at module level

    mapped = _NAME_MAP.get(first, first.lower())
    return find_template(catalog, mapped) is not None


def run_legacy(argv: list[str], catalog: dict) -> None:
    """Translate old-style invocation to cmd_new and execute it."""
    from .commands import cmd_new

    first = argv[0]
    template_name = _NAME_MAP.get(first, first.lower())

    warnings.warn(
        f"'pynewproject {first} ...' is deprecated. "
        f"Use 'pynewproject new {template_name} ...' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    print(
        f"[deprecated] Use: pynewproject new {template_name} ...",
        file=sys.stderr,
    )

    data_args = [arg for arg in argv[1:] if "=" in arg]

    args = SimpleNamespace(
        template=template_name,
        output=".",
        ref=None,
        defaults=bool(data_args),
        data=data_args,
    )
    cmd_new(args)
