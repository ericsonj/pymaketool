"""env.py — built-in .env file support for pymaketool.

Usage in Makefile.py (module-level, before @Makeclass):
    from pymakelib import load_dotenv, resolve_env

    load_dotenv()                              # loads .env from cwd (silent if missing)
    XC32 = resolve_env('XC32_PATH', '/opt/microchip/xc32/v4.60/bin/')

Or declare env_file on a ProjectConfig subclass for automatic loading:
    @Makeclass
    class Build(ProjectConfig):
        env_file = '.env'
        ...

Priority order (highest → lowest):
    1. Shell environment variables  (already in os.environ)
    2. .env file values             (loaded by load_dotenv)
    3. Default passed to resolve_env()
"""

import os
from pathlib import Path


def load_dotenv(path: str = '.env') -> None:
    """Load variables from a .env file into os.environ.

    Existing shell-level variables are NOT overwritten (override=False).
    Silent if the file does not exist.

    Args:
        path: path to the .env file, relative to cwd or absolute (default: '.env')
    """
    try:
        from dotenv import load_dotenv as _load
        _load(dotenv_path=Path(path), override=False)
    except ImportError:
        pass  # python-dotenv not installed — skip silently


def resolve_env(key: str, default: str = '') -> str:
    """Return the effective value for key, expanding shell variables and ~.

    Falls back to default if the key is not set in the environment.

    Args:
        key:     environment variable name
        default: fallback value; supports ~ and $VAR expansion

    Returns:
        str: resolved value
    """
    return os.path.expandvars(os.path.expanduser(os.environ.get(key, default)))
