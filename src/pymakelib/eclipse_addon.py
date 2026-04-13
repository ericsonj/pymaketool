import warnings
from pathlib import Path
import importlib.resources

from .addon import AddonAbstract
from . import eclipse_cproject as cp
from . import preconts as K


def _resolve_template(name: str, config_dir: Path) -> str:
    """Return the path to an Eclipse template file.

    Resolution order:
    1. ``config_dir/<name>``          — user-customized (e.g. pymake/.cproject_template)
    2. ``.pymakeproj/<name>``         — legacy location (emits DeprecationWarning)
    3. Bundled package resource       — zero-setup default, always available

    Returns the resolved path as a string suitable for ``open()``.
    For the bundled resource, the file is written into ``config_dir`` and that
    path is returned so callers can treat all cases uniformly.
    """
    # 1. config_dir (e.g. pymake/)
    candidate = config_dir / name
    if candidate.exists():
        return str(candidate)

    # 2. Legacy .pymakeproj/
    legacy = Path(K.PYMAKEPROJ) / name
    if legacy.exists():
        warnings.warn(
            f"\n[pymaketool] Eclipse template found in legacy location: {legacy}\n"
            f"  Consider moving it to {config_dir / name}\n"
            f"  The .pymakeproj directory is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=3,
        )
        return str(legacy)

    # 3. Bundled package resource — materialise to config_dir on first use
    pkg = importlib.resources.files("pymakelib.resources.templates.eclipse")
    bundled = pkg / name
    dest = config_dir / name
    dest.write_text(bundled.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[pymaketool] Created Eclipse template: {dest}")
    return str(dest)


class EclipseAddon(AddonAbstract):
    """Generate Eclipse CDT project files (.cproject, .settings/language.settings.xml).

    Templates are resolved in this order:
      1. ``<config_dir>/.cproject_template`` / ``<config_dir>/.language.settings_template``
      2. ``.pymakeproj/`` (legacy, emits DeprecationWarning)
      3. Bundled defaults (written to ``config_dir/`` on first use so users can customise)
    """

    def init(self):
        config_dir = Path(self.projectSettings.get("C_CONFIG_DIR", "."))
        self.generateLanguageSettings(config_dir)
        self.generateCProject(config_dir)

    def generateLanguageSettings(self, config_dir: Path):
        template_path = _resolve_template(".language.settings_template", config_dir)
        cp.generate_languageSettings(self.compilerSettings, template_path=template_path)

    def generateCProject(self, config_dir: Path):
        template_path = _resolve_template(".cproject_template", config_dir)
        cp.generate_cproject(self.projectSettings, template_path=template_path)