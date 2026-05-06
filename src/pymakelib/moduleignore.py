"""Module discovery ignore management with gitignore-style semantics.

Supports:
- Reading .gitignore by default
- Reading .moduleignore (pymake/.moduleignore preferred, fallback to root)
- Makefile.py control options (use_gitignore, ignore_list)
- Full gitwildmatch pattern syntax via pathspec
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import pathspec
from . import preconts
from . import Logger

log = Logger.getLogger()


class IgnoreSpec:
    """Compiled ignore pattern matcher using gitignore semantics."""
    
    def __init__(self, spec: pathspec.PathSpec):
        self._spec = spec
    
    def match_file(self, path: str) -> bool:
        """Check if a path should be ignored.
        
        Args:
            path: Project-relative POSIX-style path (e.g., 'app/mk.py')
        
        Returns:
            True if the path matches any ignore pattern
        """
        return self._spec.match_file(path)
    
    def __bool__(self):
        """Return False if no patterns (allows `if ignore_spec:` checks)."""
        return bool(self._spec.patterns)


def _normalize_path(path: Path, project_root: Path) -> str:
    """Normalize a path to project-relative POSIX style.
    
    Args:
        path: Absolute or relative path
        project_root: Project root directory
    
    Returns:
        Project-relative path with forward slashes
    """
    try:
        if path.is_absolute():
            rel_path = path.relative_to(project_root)
        else:
            rel_path = path
        # Convert to POSIX style (forward slashes)
        return str(rel_path).replace('\\', '/')
    except (ValueError, OSError):
        # Path is outside project root or invalid
        log.debug(f"Path {path} could not be normalized relative to {project_root}")
        return str(path).replace('\\', '/')


def _read_patterns_from_file(file_path: Path) -> List[str]:
    """Read ignore patterns from a file, filtering comments and blank lines.
    
    Args:
        file_path: Path to ignore file
    
    Returns:
        List of pattern strings (non-empty, non-comment lines)
    """
    patterns = []
    if not file_path.exists():
        return patterns
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n\r')
                # Skip blank lines and comments
                if line and not line.lstrip().startswith('#'):
                    patterns.append(line)
        log.debug(f"Loaded {len(patterns)} patterns from {file_path}")
    except Exception as e:
        log.debug(f"Could not read ignore file {file_path}: {e}")
    
    return patterns


def _resolve_ignore_file_paths(
    project_root: Path,
    config_dir: Optional[Path] = None
) -> tuple[Optional[Path], Optional[Path]]:
    """Resolve paths to .moduleignore and .gitignore files.
    
    Args:
        project_root: Project root directory
        config_dir: Config directory (pymake/ or project root)
    
    Returns:
        Tuple of (moduleignore_path, gitignore_path), either can be None
    """
    # .moduleignore: prefer config_dir (pymake/), fallback to root
    moduleignore_path = None
    if config_dir and (config_dir / preconts.MODULEIGNORE_FILE).exists():
        moduleignore_path = config_dir / preconts.MODULEIGNORE_FILE
    elif (project_root / preconts.MODULEIGNORE_FILE).exists():
        moduleignore_path = project_root / preconts.MODULEIGNORE_FILE
    
    # .gitignore: always at project root
    gitignore_path = project_root / '.gitignore'
    if not gitignore_path.exists():
        gitignore_path = None
    
    return moduleignore_path, gitignore_path


def read_ignore_spec(
    project_root: Path,
    config_dir: Optional[Path] = None,
    makefile_config: Optional[Dict[str, Any]] = None
) -> IgnoreSpec:
    """Read and compile ignore patterns from all sources.
    
    Merge order (later sources can override with negation):
    1. .gitignore (if use_gitignore not disabled)
    2. .moduleignore (pymake/.moduleignore or root .moduleignore)
    3. Makefile.py ignore_list (if provided)
    
    Args:
        project_root: Project root directory
        config_dir: Config directory (pymake/ or project root)
        makefile_config: Optional config from Makefile.py with keys:
            - 'use_gitignore': bool (default True)
            - 'ignore_list': List[str] (additional patterns)
    
    Returns:
        Compiled IgnoreSpec matcher
    """
    if makefile_config is None:
        makefile_config = {}
    
    use_gitignore = makefile_config.get('use_gitignore', True)
    extra_patterns = makefile_config.get('ignore_list', [])
    
    all_patterns = []
    
    moduleignore_path, gitignore_path = _resolve_ignore_file_paths(
        project_root, config_dir
    )
    
    # 1. Load .gitignore if enabled
    if use_gitignore and gitignore_path:
        patterns = _read_patterns_from_file(gitignore_path)
        all_patterns.extend(patterns)
        log.debug(f"Loaded {len(patterns)} patterns from .gitignore")
    
    # 2. Load .moduleignore
    if moduleignore_path:
        patterns = _read_patterns_from_file(moduleignore_path)
        all_patterns.extend(patterns)
        log.debug(f"Loaded {len(patterns)} patterns from {moduleignore_path}")
    
    # 3. Add Makefile.py patterns
    if extra_patterns:
        all_patterns.extend(extra_patterns)
        log.debug(f"Added {len(extra_patterns)} patterns from Makefile.py")
    
    # Compile with gitwildmatch semantics
    if all_patterns:
        spec = pathspec.PathSpec.from_lines('gitignore', all_patterns)
        log.debug(f"Compiled {len(all_patterns)} total ignore patterns")
    else:
        spec = pathspec.PathSpec.from_lines('gitignore', [])
    
    return IgnoreSpec(spec)


# Legacy API compatibility functions


def readIgnoreFile(file=Path(preconts.MODULEIGNORE_FILE)):
    """Legacy function for backward compatibility.
    
    Returns list of Path objects from ignore file (exact-match legacy behavior).
    Prefer using read_ignore_spec() for new code.
    """
    ignorelist = []
    try:
        with open(str(file), 'r', encoding='utf-8') as ignoreFile:
            for line in ignoreFile:
                line = line.rstrip()
                if line and not line.lstrip().startswith('#'):
                    ignorelist.append(Path(line))
    except:
        pass
    return ignorelist


def writeIgnoreFile(ignoreList: list, file=Path(preconts.MODULEIGNORE_FILE)):
    """Legacy function for backward compatibility.
    
    Writes ignore patterns to file, merging with existing content.
    """
    currList = readIgnoreFile(file)

    try:
        with open(str(file), "w", encoding='utf-8') as ignoreFile:
            for item in ignoreList:
                if Path(item) not in currList:
                    currList.append(item)
            
            ignores = list(map(str, currList))
            ignores = [x + '\n' for x in ignores]
            ignoreFile.writelines(ignores)
    except Exception as e:
        print(e)