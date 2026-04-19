"""CLI command implementations for pynewproject."""

import os
import shutil
import sys
from pathlib import Path

from copier import run_copy, run_update

from .catalog import fetch_catalog, find_template

# Override via env var for local development or CI:
#   PYNEWPROJECT_TEMPLATES_REPO=/path/to/local/pymaketool-templates
#   PYNEWPROJECT_TEMPLATES_REPO=https://github.com/yourfork/pymaketool-templates.git
TEMPLATE_REPO = os.environ.get(
    "PYNEWPROJECT_TEMPLATES_REPO",
    "https://github.com/ericsonj/pymaketool-templates.git",
)

# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def cmd_list(args) -> None:
    catalog = fetch_catalog(refresh=getattr(args, "refresh", False))
    templates = list(catalog.get("templates", []))

    if getattr(args, "category", None):
        templates = [t for t in templates if t.get("category") == args.category]
    if getattr(args, "tag", None):
        for tag in args.tag:
            templates = [t for t in templates if tag in t.get("tags", [])]

    if getattr(args, "json", False):
        import json
        print(json.dumps(templates, indent=2))
        return

    if not templates:
        print("No templates found matching your filters.")
        return

    print(f"\n  {'NAME':<20} {'CATEGORY':<12} {'DESCRIPTION':<46} {'VERSION'}")
    print(f"  {'-'*20} {'-'*12} {'-'*46} {'-'*7}")
    for t in templates:
        print(
            f"  {t['name']:<20} {t.get('category',''):<12} "
            f"{t.get('description',''):<46} {t.get('version','')}"
        )
    print()


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------

def cmd_new(args) -> None:
    catalog = fetch_catalog()
    tmpl = find_template(catalog, args.template)
    if not tmpl:
        print(
            f"Template '{args.template}' not found. "
            f"Run 'pynewproject list' to see available templates."
        )
        sys.exit(1)

    data: dict[str, str] = {}
    for item in getattr(args, "data", []):
        key, _, value = item.partition("=")
        data[key.strip()] = value.strip()

    ref = getattr(args, "ref", None) or tmpl.get("version")
    run_copy(
        src_path=TEMPLATE_REPO,
        dst_path=args.output,
        subdirectory=tmpl["subdirectory"],
        vcs_ref=ref,
        data=data or None,
        defaults=getattr(args, "defaults", False),
        unsafe=True,
        overwrite=False,
        cleanup_on_error=True,
    )

    project_name = data.get("project_name", args.template)
    print(f"\nProject '{project_name}' created successfully!")
    print("Next steps:")
    print(f"  cd {project_name}")
    print("  make")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

def cmd_update(args) -> None:
    dst = Path(getattr(args, "path", "."))
    answers_file = dst / ".copier-answers.yml"
    if not answers_file.exists():
        print(
            f"No .copier-answers.yml found in '{dst}'.\n"
            "This project was not created with pynewproject (copier edition).\n"
            "See the migration guide: https://github.com/ericsonj/pymaketool-templates#migration"
        )
        sys.exit(1)

    run_update(
        dst_path=str(dst),
        vcs_ref=getattr(args, "ref", None),
        conflict=getattr(args, "conflict", "inline"),
        unsafe=True,
        skip_answered=True,
        overwrite=True,
    )
    print("Project updated successfully.")


# ---------------------------------------------------------------------------
# info
# ---------------------------------------------------------------------------

def cmd_info(args) -> None:
    catalog = fetch_catalog()
    tmpl = find_template(catalog, args.template)
    if not tmpl:
        print(f"Template '{args.template}' not found.")
        sys.exit(1)

    print(f"\n  Name:        {tmpl.get('display_name', tmpl['name'])}")
    print(f"  Description: {tmpl.get('description', '')}")
    print(f"  Category:    {tmpl.get('category', '')}")
    print(f"  Tags:        {', '.join(tmpl.get('tags', []))}")
    print(f"  Version:     {tmpl.get('version', '')}")
    print(f"  Subdirectory: {tmpl.get('subdirectory', '')}")
    print(f"  Min pymaketool: {tmpl.get('min_pymaketool', '')}")
    print()


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------

def cmd_doctor(_args) -> None:
    import importlib.metadata

    checks: list[tuple[str, bool | str]] = []

    # Python version
    import sys as _sys
    py_ok = _sys.version_info >= (3, 10)
    checks.append(("Python >= 3.10", py_ok))

    # git
    checks.append(("git on PATH", shutil.which("git") is not None))

    # copier version
    try:
        ver = importlib.metadata.version("copier")
        from packaging.version import Version
        checks.append(("copier >= 9.0.0", Version(ver) >= Version("9.0.0")))
    except Exception:
        checks.append(("copier installed", False))

    # network
    try:
        from urllib.request import urlopen
        urlopen("https://raw.githubusercontent.com", timeout=5)
        checks.append(("Network (github.com)", True))
    except Exception:
        checks.append(("Network (github.com)", False))

    # gcc
    checks.append(("gcc on PATH", shutil.which("gcc") is not None))
    checks.append(("arm-none-eabi-gcc on PATH", shutil.which("arm-none-eabi-gcc") is not None))

    print()
    for name, ok in checks:
        status = "OK  " if ok else "FAIL"
        print(f"  [{status}] {name}")
    print()
