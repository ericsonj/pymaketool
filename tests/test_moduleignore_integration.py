"""Integration tests for module discovery with ignore functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys


class TestDiscoveryWithIgnore(unittest.TestCase):
    """Integration test for module discovery filtering via ignore patterns."""

    def setUp(self):
        """Create a temporary test project."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        
        # Add project root to sys.path
        sys.path.insert(0, str(self.project_root))

    def tearDown(self):
        """Clean up temporary project."""
        # Remove from sys.path
        if str(self.project_root) in sys.path:
            sys.path.remove(str(self.project_root))
        
        # Clean up global ProjectInstance to avoid polluting other tests
        import pymakelib
        pymakelib.ProjectInstance = None
        
        self.temp_dir.cleanup()

    def _create_minimal_makefile_py(self, ignore_config=None):
        """Create a minimal Makefile.py for testing."""
        pymake_dir = self.project_root / 'pymake'
        pymake_dir.mkdir(exist_ok=True)
        
        makefile_content = '''
from pymakelib import ProjectConfig, Makeclass, MKVARS, Target
from pymakelib.toolchain import get_gcc_linux

@Makeclass
class Build(ProjectConfig):
    name = 'testproject'
    compiler_set = get_gcc_linux()
'''
        
        if ignore_config:
            if 'use_gitignore' in ignore_config:
                makefile_content += f"\n    use_gitignore = {ignore_config['use_gitignore']}"
            if 'ignore_list' in ignore_config:
                patterns_str = str(ignore_config['ignore_list'])
                makefile_content += f"\n    ignore_list = {patterns_str}"
        
        makefile_content += '''
    
    def targets(self):
        return {
            'TARGET': Target(
                file='build/testproject',
                script=[MKVARS.LD, '-o', '$@', MKVARS.OBJECTS],
                logkey='OUT'
            )
        }
'''
        
        (pymake_dir / 'Makefile.py').write_text(makefile_content)

    def _create_module_file(self, path):
        """Create a minimal module file."""
        module_path = self.project_root / path
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text('from pm import mk\nmk()\n')

    def test_discovery_with_moduleignore_wildcard(self):
        """Test that wildcard patterns in .moduleignore filter modules."""
        # Create Makefile.py
        self._create_minimal_makefile_py()
        
        # Create modules
        self._create_module_file('app/mk.py')
        self._create_module_file('test_app_mk.py')
        self._create_module_file('test_lib_mk.py')
        
        # Create .moduleignore with wildcard
        (self.project_root / 'pymake' / '.moduleignore').write_text('test_*')
        
        # Import and run discovery
        from pymakelib import moduleignore, prelib
        
        # Resolve config
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        # Read ignore spec
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir
        )
        
        # Test patterns
        self.assertTrue(ignore_spec.match_file('test_app_mk.py'))
        self.assertTrue(ignore_spec.match_file('test_lib_mk.py'))
        self.assertFalse(ignore_spec.match_file('app/mk.py'))

    def test_discovery_with_gitignore_by_default(self):
        """Test that .gitignore is read by default."""
        # Create Makefile.py
        self._create_minimal_makefile_py()
        
        # Create .gitignore
        (self.project_root / '.gitignore').write_text('build/\n*.tmp')
        
        # Import and run discovery
        from pymakelib import moduleignore, prelib
        
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir
        )
        
        # Test gitignore patterns are active
        self.assertTrue(ignore_spec.match_file('build/app_mk.py'))
        self.assertTrue(ignore_spec.match_file('test.tmp'))

    def test_discovery_can_disable_gitignore(self):
        """Test that use_gitignore=False disables .gitignore."""
        # Create Makefile.py with use_gitignore=False
        self._create_minimal_makefile_py({'use_gitignore': False})
        
        # Create .gitignore
        (self.project_root / '.gitignore').write_text('build/')
        
        # Import and run discovery
        from pymakelib import moduleignore, prelib
        
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        # Get project instance to read config
        prelib.read_Makefilepy(config_dir=config_dir)
        projectInstance = prelib.getProjectInstance()
        ignore_config = projectInstance.getIgnoreConfig()
        
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir,
            makefile_config=ignore_config
        )
        
        # .gitignore patterns should not be active
        self.assertFalse(ignore_spec.match_file('build/app_mk.py'))

    def test_discovery_with_makefile_ignore_list(self):
        """Test that ignore_list in Makefile.py adds patterns."""
        # Create Makefile.py with ignore_list
        self._create_minimal_makefile_py({
            'ignore_list': ['vendor/', 'third_party/']
        })
        
        # Import and run discovery
        from pymakelib import moduleignore, prelib
        
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        prelib.read_Makefilepy(config_dir=config_dir)
        projectInstance = prelib.getProjectInstance()
        ignore_config = projectInstance.getIgnoreConfig()
        
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir,
            makefile_config=ignore_config
        )
        
        # Makefile.py patterns should be active
        self.assertTrue(ignore_spec.match_file('vendor/ext_mk.py'))
        self.assertTrue(ignore_spec.match_file('third_party/lib_mk.py'))

    def test_discovery_with_directory_ignore(self):
        """Test that directory patterns ignore subdirectories."""
        self._create_minimal_makefile_py()
        
        # Create .moduleignore with directory pattern
        (self.project_root / 'pymake' / '.moduleignore').write_text('tests/')
        
        from pymakelib import moduleignore, prelib
        
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir
        )
        
        # Should match anything under tests/
        self.assertTrue(ignore_spec.match_file('tests/app_mk.py'))
        self.assertTrue(ignore_spec.match_file('tests/unit/lib_mk.py'))
        self.assertFalse(ignore_spec.match_file('src/test_app_mk.py'))

    def test_moduleignore_in_pymake_preferred_over_root(self):
        """Test that pymake/.moduleignore is preferred over root."""
        self._create_minimal_makefile_py()
        
        # Create both ignore files with different patterns
        (self.project_root / '.moduleignore').write_text('pattern_from_root')
        (self.project_root / 'pymake' / '.moduleignore').write_text('pattern_from_pymake')
        
        from pymakelib import moduleignore, prelib
        
        config_dir, _ = prelib.resolve_config_dir(self.project_root)
        
        ignore_spec = moduleignore.read_ignore_spec(
            self.project_root,
            config_dir=config_dir
        )
        
        # Should use pymake/.moduleignore pattern
        self.assertTrue(ignore_spec.match_file('pattern_from_pymake'))
        self.assertFalse(ignore_spec.match_file('pattern_from_root'))


if __name__ == '__main__':
    unittest.main()
