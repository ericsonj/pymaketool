"""Deprecated: use copier-based templates via pynewproject instead."""
import warnings
warnings.warn(
    "pymakelib.pynewproject_cproject is deprecated and will be removed in pymaketool 4.0.0. "
    "Use copier-based templates via pynewproject instead.",
    DeprecationWarning,
    stacklevel=2,
)

generators = [
    "pynewproject_clinuxgcc.CLinuxGCC"
]
