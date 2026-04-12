#!/usr/bin/env python3

# Copyright (c) 2020, Ericson Joseph
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of pyMakeTool nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""pymakemigrate — migrate a pymaketool legacy project to the pymake/ subdirectory layout.

Usage:
    pymakemigrate [--subdir SUBDIR] [--dry-run] [--merge-tool TOOL]

Steps performed:
  1. Verify this is a legacy project (Makefile.py at root, no subdir layout yet).
  2. Create the target subdirectory (default: pymake/).
  3. For each config/generated file:
       - Not yet at destination → move it.
       - Already at destination  → launch a merge tool so the user can reconcile.
  4. Update the root Makefile to reference <subdir>/makefile.mk instead of makefile.mk.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from pymakelib import preconts as K

# Files managed by the user (hand-written) — always migrate, never silently overwrite.
_USER_FILES = [K.MAKEFILE_PY, K.MAKEFILE_MK]

# Generated files — still move them if present so includes resolve correctly.
_GENERATED_FILES = [K.VARS_MK, K.TARGETS_MK, K.SRCS_MK]

_ALL_FILES = _USER_FILES + _GENERATED_FILES

# Ordered preference list for merge tools.
# Each entry: (executable, args-template)
# {src} = existing file at destination, {dst} = incoming file from root
_MERGE_TOOL_CANDIDATES = [
    ("meld",     ["{src}", "{dst}"]),
    ("kdiff3",   ["{src}", "{dst}"]),
    ("code",     ["--diff", "{src}", "{dst}"]),
    ("vimdiff",  ["{src}", "{dst}"]),
    ("nvim",     ["-d", "{src}", "{dst}"]),
    ("vim",      ["-d", "{src}", "{dst}"]),
]


def _find_merge_tool(override: str = None) -> tuple[str, list[str]] | None:
    """Return (executable, args_template) for the first available merge tool."""
    if override:
        return override, ["{src}", "{dst}"]

    env_tool = os.environ.get("MERGE_TOOL") or os.environ.get("PYMAKE_MERGE_TOOL")
    if env_tool:
        return env_tool, ["{src}", "{dst}"]

    for exe, args in _MERGE_TOOL_CANDIDATES:
        if shutil.which(exe):
            return exe, args
    return None


def _run_merge(tool: str, args_template: list[str], src: Path, dst: Path) -> None:
    """Launch the merge tool with src (destination copy) and dst (root copy)."""
    cmd = [tool] + [
        a.format(src=str(src), dst=str(dst)) for a in args_template
    ]
    print(f"  Launching: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print(f"  [ERROR] Merge tool '{tool}' not found. Skipping merge for {dst.name}.", file=sys.stderr)


def _patch_makefile_mk(subdir_path: Path, subdir: str, dry_run: bool) -> bool:
    """Patch include directives inside <subdir>/makefile.mk after it has been moved.

    In the legacy layout these includes were relative to the project root:
        include vars.mk
        include srcs.mk
        include targets.mk

    After moving into the subdir, make still evaluates includes relative to the
    directory where 'make' is invoked (the project root), so they must become:
        include <subdir>/vars.mk
        ...

    Returns True if the file was (or would be) changed.
    """
    makefile_mk = subdir_path / K.MAKEFILE_MK
    if not makefile_mk.exists():
        print(f"  [SKIP] {subdir}/makefile.mk not found — skipping patch.")
        return False

    original = makefile_mk.read_text(encoding="utf-8")

    # Replace every bare (unprefixed) reference to each managed .mk file.
    # This covers: include directives, $(wildcard ...), error guards, variable
    # assignments, comments — anything that still points at the project root.
    # A reference is "bare" when it is NOT already preceded by a path separator.
    mk_files = [K.VARS_MK, K.SRCS_MK, K.TARGETS_MK]
    patched = original
    for mk in mk_files:
        patched = re.sub(
            rf"(?<![/\w]){re.escape(mk)}",
            f"{subdir}/{mk}",
            patched,
        )

    if patched == original:
        print(f"  [OK]   {subdir}/makefile.mk references already correct or no match found.")
        return False

    if dry_run:
        for mk in mk_files:
            print(f"  [DRY]  Would patch {subdir}/makefile.mk: {mk} → {subdir}/{mk} (all occurrences)")
        return True

    makefile_mk.write_text(patched, encoding="utf-8")
    for mk in mk_files:
        print(f"  [OK]   Patched {subdir}/makefile.mk: {mk} → {subdir}/{mk} (all occurrences)")
    return True


def _patch_root_makefile(root: Path, subdir: str, dry_run: bool) -> bool:
    """Rewrite root Makefile so it points at <subdir>/makefile.mk instead of makefile.mk.

    Returns True if the file was (or would be) changed.
    """
    makefile = root / "Makefile"
    if not makefile.exists():
        print("  [SKIP] Root Makefile not found — skipping patch.")
        return False

    original = makefile.read_text(encoding="utf-8")

    # Replace  -f makefile.mk  with  -f <subdir>/makefile.mk
    # Be conservative: only match the bare filename, not an already-prefixed path.
    patched = re.sub(
        r"(-f\s+)(?![\w/]*/)makefile\.mk",
        rf"\g<1>{subdir}/makefile.mk",
        original,
    )

    if patched == original:
        print("  [OK]   Root Makefile already references the subdir or no match found.")
        return False

    if dry_run:
        print(f"  [DRY]  Would patch root Makefile: -f makefile.mk → -f {subdir}/makefile.mk")
        return True

    makefile.write_text(patched, encoding="utf-8")
    print(f"  [OK]   Patched root Makefile: -f makefile.mk → -f {subdir}/makefile.mk")
    return True


def migrate(subdir: str = "pymake", dry_run: bool = False, merge_tool: str = None) -> int:
    """Run the migration. Returns 0 on success, non-zero on error."""
    root = Path(".").resolve()

    # --- Pre-flight checks ---------------------------------------------------
    if not (root / K.PYMAKEPROJ).exists():
        print("[ERROR] Not a pymaketool project (.pymakeproj directory not found).", file=sys.stderr)
        return 1

    legacy_makefile_py = root / K.MAKEFILE_PY
    if not legacy_makefile_py.exists():
        print(
            f"[ERROR] {K.MAKEFILE_PY} not found at project root.\n"
            f"        This project may already be using the new layout or was never initialised.",
            file=sys.stderr,
        )
        return 1

    subdir_path = root / subdir
    if (subdir_path / K.MAKEFILE_PY).exists():
        print(
            f"[INFO] {subdir}/{K.MAKEFILE_PY} already exists — project appears to be on the new layout.\n"
            f"       Run with --force to re-run the migration anyway (not yet supported).",
            file=sys.stderr,
        )
        return 1

    # --- Locate merge tool ---------------------------------------------------
    tool_exe, tool_args = _find_merge_tool(merge_tool) or (None, None)
    if tool_exe:
        print(f"Merge tool: {tool_exe}")
    else:
        print(
            "[WARN] No merge tool found. Files that already exist at the destination will be SKIPPED.\n"
            "       Install meld, kdiff3, vimdiff, or set MERGE_TOOL env var to enable merging.",
            file=sys.stderr,
        )

    # --- Create subdirectory -------------------------------------------------
    print(f"\nMigrating to: {subdir}/")
    if not dry_run:
        subdir_path.mkdir(exist_ok=True)
    else:
        print(f"  [DRY]  Would create directory: {subdir}/")

    # --- Move files ----------------------------------------------------------
    print()
    moved, merged, skipped = [], [], []

    for filename in _ALL_FILES:
        src = root / filename
        dst = subdir_path / filename

        if not src.exists():
            print(f"  [SKIP] {filename} — not found at root (nothing to migrate)")
            skipped.append(filename)
            continue

        if dst.exists():
            if tool_exe:
                print(f"  [MERGE] {filename} — exists in both root and {subdir}/")
                if not dry_run:
                    _run_merge(tool_exe, tool_args, dst, src)
                else:
                    print(f"          [DRY] Would launch merge for {filename}")
                merged.append(filename)
            else:
                print(f"  [SKIP] {filename} — already exists at destination and no merge tool available")
                skipped.append(filename)
            continue

        # Clean move: destination does not yet exist.
        print(f"  [MOVE] {filename}  →  {subdir}/{filename}")
        if not dry_run:
            shutil.move(str(src), str(dst))
        moved.append(filename)

    # --- Patch makefile.mk includes (must run after the file is in place) ----
    print()
    _patch_makefile_mk(subdir_path, subdir, dry_run)

    # --- Patch root Makefile -------------------------------------------------
    print()
    _patch_root_makefile(root, subdir, dry_run)

    # --- Summary -------------------------------------------------------------
    print()
    print("=" * 52)
    print("Migration summary")
    print("=" * 52)
    print(f"  Moved   : {', '.join(moved) if moved else '(none)'}")
    print(f"  Merged  : {', '.join(merged) if merged else '(none)'}")
    print(f"  Skipped : {', '.join(skipped) if skipped else '(none)'}")
    if dry_run:
        print()
        print("  DRY RUN — no files were changed.")

    if merged:
        print()
        print(
            "[NOTE] After merging, review the files in the merge tool and save the\n"
            "       destination copy inside the subdir. The root copies were NOT removed\n"
            "       automatically. Delete them manually once you are satisfied:\n"
        )
        for f in merged:
            print(f"         rm {f}")

    return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="pymakemigrate",
        description="Migrate a pymaketool legacy project to the pymake/ subdirectory layout.",
    )
    parser.add_argument(
        "--subdir",
        default=K.MAKEFILE_SUBDIR_CANDIDATES[0],
        help=f"Target subdirectory name (default: {K.MAKEFILE_SUBDIR_CANDIDATES[0]})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making any changes.",
    )
    parser.add_argument(
        "--merge-tool",
        metavar="TOOL",
        default=None,
        help="Merge tool to use when a file already exists at the destination "
             "(e.g. meld, vimdiff). Overrides MERGE_TOOL env var.",
    )
    args = parser.parse_args()
    sys.exit(migrate(subdir=args.subdir, dry_run=args.dry_run, merge_tool=args.merge_tool))
