#!/usr/bin/env python3

# Copyright (c) 2021, Ericson Joseph
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

import argparse
import signal
import sys

from pymakelib.version import get_version

from .catalog import fetch_catalog
from .commands import cmd_doctor, cmd_info, cmd_list, cmd_new, cmd_update
from .legacy import detect_legacy, run_legacy


def _signal_handler(_sig, _frame):
    sys.exit(0)


signal.signal(signal.SIGINT, _signal_handler)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pynewproject",
        description="Scaffold and manage pymaketool C/C++ projects using copier templates.",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # -- list -----------------------------------------------------------------
    p_list = sub.add_parser("list", help="List available project templates")
    p_list.add_argument(
        "--category", "-c", help="Filter by category (linux, embedded, rtos)"
    )
    p_list.add_argument(
        "--tag", "-t", action="append", metavar="TAG",
        help="Filter by tag (repeatable: -t gcc -t arm)"
    )
    p_list.add_argument(
        "--refresh", action="store_true", help="Force re-fetch catalog (bypass cache)"
    )
    p_list.add_argument(
        "--json", action="store_true", help="Output catalog as JSON"
    )

    # -- new ------------------------------------------------------------------
    p_new = sub.add_parser("new", help="Create a new project from a template")
    p_new.add_argument("template", help="Template name (see 'pynewproject list')")
    p_new.add_argument(
        "--output", "-o", default=".", metavar="DIR",
        help="Directory in which to create the project (default: current dir)"
    )
    p_new.add_argument(
        "--ref", "-r", metavar="TAG",
        help="Template version / git tag (default: latest)"
    )
    p_new.add_argument(
        "--defaults", action="store_true",
        help="Accept all default values without prompting"
    )
    p_new.add_argument(
        "--data", "-d", action="append", default=[], metavar="KEY=VALUE",
        help="Pass answers non-interactively (repeatable: -d author=You -d project_name=app)"
    )

    # -- update ---------------------------------------------------------------
    p_upd = sub.add_parser("update", help="Update an existing project to latest template version")
    p_upd.add_argument(
        "path", nargs="?", default=".",
        help="Project directory to update (default: current dir)"
    )
    p_upd.add_argument(
        "--ref", "-r", metavar="TAG",
        help="Target template version / git tag (default: latest)"
    )
    p_upd.add_argument(
        "--conflict", choices=["inline", "rej"], default="inline",
        help="Conflict resolution mode (default: inline)"
    )

    # -- info -----------------------------------------------------------------
    p_info = sub.add_parser("info", help="Show details about a template")
    p_info.add_argument("template", help="Template name")

    # -- doctor ---------------------------------------------------------------
    sub.add_parser("doctor", help="Check environment and tool availability")

    return parser


def _looks_like_legacy(argv: list[str]) -> bool:
    """Quick pre-check: is the first arg a bare word that could be a legacy generator name?"""
    _KNOWN = {"list", "new", "update", "info", "doctor", "-h", "--help", "-v", "--version"}
    return bool(argv) and not argv[0].startswith("-") and argv[0] not in _KNOWN


def main():
    # Only fetch the catalog when the first arg might be a legacy generator name.
    # This avoids a network call (and any warning) for normal subcommand usage.
    if len(sys.argv) > 1 and _looks_like_legacy(sys.argv[1:]):
        try:
            catalog = fetch_catalog()
        except Exception:
            catalog = {"templates": []}
        if detect_legacy(sys.argv[1:], catalog):
            run_legacy(sys.argv[1:], catalog)
            return

    parser = _build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "list": cmd_list,
        "new": cmd_new,
        "update": cmd_update,
        "info": cmd_info,
        "doctor": cmd_doctor,
    }
    dispatch[args.command](args)
