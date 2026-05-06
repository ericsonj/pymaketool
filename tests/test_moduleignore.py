"""Tests for moduleignore module with gitignore-style semantics."""

import unittest
import tempfile
from pathlib import Path
from pymakelib import moduleignore


class TestIgnorePatternParsing(unittest.TestCase):
    """Test pattern file parsing (comments, blanks, etc.)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_read_patterns_skips_blank_lines(self):
        """Blank lines should be ignored."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('\n\napp_mk.py\n\n\ntest/\n')
        
        patterns = moduleignore._read_patterns_from_file(ignore_file)
        self.assertEqual(2, len(patterns))
        self.assertIn('app_mk.py', patterns)
        self.assertIn('test/', patterns)

    def test_read_patterns_skips_comments(self):
        """Lines starting with # should be ignored."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('# Comment\napp_mk.py\n  # Indented comment\ntest/')
        
        patterns = moduleignore._read_patterns_from_file(ignore_file)
        self.assertEqual(2, len(patterns))
        self.assertIn('app_mk.py', patterns)
        self.assertIn('test/', patterns)

    def test_read_patterns_preserves_trailing_slash(self):
        """Trailing slashes should be preserved for directory matching."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('build/\ntest/')
        
        patterns = moduleignore._read_patterns_from_file(ignore_file)
        self.assertEqual(2, len(patterns))
        self.assertIn('build/', patterns)
        self.assertIn('test/', patterns)

    def test_read_patterns_nonexistent_file_returns_empty(self):
        """Non-existent file should return empty list."""
        patterns = moduleignore._read_patterns_from_file(
            self.project_root / 'nonexistent.txt'
        )
        self.assertEqual(0, len(patterns))


class TestIgnoreSpecMatching(unittest.TestCase):
    """Test gitignore-style pattern matching."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_exact_path_match(self):
        """Exact paths should match."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('app_mk.py')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertTrue(spec.match_file('app_mk.py'))
        self.assertFalse(spec.match_file('lib_mk.py'))

    def test_wildcard_asterisk(self):
        """Wildcard * should match multiple characters."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('test_*')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertTrue(spec.match_file('test_app_mk.py'))
        self.assertTrue(spec.match_file('test_mk.py'))
        self.assertFalse(spec.match_file('app_mk.py'))

    def test_directory_pattern(self):
        """Trailing slash should match directories and their contents."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('build/')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertTrue(spec.match_file('build/app_mk.py'))
        self.assertTrue(spec.match_file('build/lib/test_mk.py'))
        self.assertFalse(spec.match_file('src/build_mk.py'))

    def test_recursive_wildcard(self):
        """** should match any depth."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('**/test_*')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertTrue(spec.match_file('test_app_mk.py'))
        self.assertTrue(spec.match_file('src/test_util_mk.py'))
        self.assertTrue(spec.match_file('src/lib/test_helper_mk.py'))
        self.assertFalse(spec.match_file('src/app_mk.py'))

    def test_negation_pattern(self):
        """! should negate a previous pattern."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('*.py\n!main.py')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertTrue(spec.match_file('test.py'))
        self.assertFalse(spec.match_file('main.py'))

    def test_empty_spec_matches_nothing(self):
        """Empty ignore spec should match nothing."""
        spec = moduleignore.read_ignore_spec(self.project_root)
        self.assertFalse(spec.match_file('app_mk.py'))
        self.assertFalse(spec.match_file('test/lib_mk.py'))
        # Empty spec should evaluate to False
        self.assertFalse(bool(spec))


class TestIgnoreFileLocation(unittest.TestCase):
    """Test .moduleignore file location resolution."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_prefers_pymake_location(self):
        """Should prefer pymake/.moduleignore over root."""
        pymake_dir = self.project_root / 'pymake'
        pymake_dir.mkdir()
        
        # Create both files with different content
        (pymake_dir / '.moduleignore').write_text('from_pymake')
        (self.project_root / '.moduleignore').write_text('from_root')
        
        moduleignore_path, _ = moduleignore._resolve_ignore_file_paths(
            self.project_root, pymake_dir
        )
        
        self.assertEqual(moduleignore_path, pymake_dir / '.moduleignore')

    def test_fallback_to_root_location(self):
        """Should fallback to root .moduleignore if pymake/ doesn't have it."""
        pymake_dir = self.project_root / 'pymake'
        pymake_dir.mkdir()
        
        (self.project_root / '.moduleignore').write_text('from_root')
        
        moduleignore_path, _ = moduleignore._resolve_ignore_file_paths(
            self.project_root, pymake_dir
        )
        
        self.assertEqual(moduleignore_path, self.project_root / '.moduleignore')

    def test_no_moduleignore_returns_none(self):
        """Should return None if no .moduleignore exists."""
        moduleignore_path, _ = moduleignore._resolve_ignore_file_paths(
            self.project_root, None
        )
        
        self.assertIsNone(moduleignore_path)

    def test_gitignore_resolved_at_root(self):
        """Should find .gitignore at project root."""
        (self.project_root / '.gitignore').write_text('*.o')
        
        _, gitignore_path = moduleignore._resolve_ignore_file_paths(
            self.project_root, None
        )
        
        self.assertEqual(gitignore_path, self.project_root / '.gitignore')


class TestIgnoreSourceMerging(unittest.TestCase):
    """Test merging patterns from multiple sources."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_merges_gitignore_and_moduleignore(self):
        """Should merge patterns from both files."""
        (self.project_root / '.gitignore').write_text('*.o\nbuild/')
        (self.project_root / '.moduleignore').write_text('test_*')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        
        # All patterns should be active
        self.assertTrue(spec.match_file('main.o'))
        self.assertTrue(spec.match_file('build/app_mk.py'))
        self.assertTrue(spec.match_file('test_mk.py'))

    def test_moduleignore_can_override_gitignore(self):
        """Moduleignore patterns (loaded later) can negate gitignore."""
        (self.project_root / '.gitignore').write_text('*.py')
        (self.project_root / '.moduleignore').write_text('!*_mk.py')
        
        spec = moduleignore.read_ignore_spec(self.project_root)
        
        # Regular .py ignored, but _mk.py allowed
        self.assertTrue(spec.match_file('test.py'))
        self.assertFalse(spec.match_file('app_mk.py'))

    def test_makefile_config_adds_extra_patterns(self):
        """Makefile.py ignore_list should add patterns."""
        (self.project_root / '.moduleignore').write_text('test_*')
        
        config = {'ignore_list': ['vendor/', 'third_party/']}
        spec = moduleignore.read_ignore_spec(
            self.project_root,
            makefile_config=config
        )
        
        self.assertTrue(spec.match_file('test_mk.py'))
        self.assertTrue(spec.match_file('vendor/lib_mk.py'))
        self.assertTrue(spec.match_file('third_party/ext_mk.py'))

    def test_use_gitignore_false_disables_gitignore(self):
        """use_gitignore=False should skip .gitignore."""
        (self.project_root / '.gitignore').write_text('*.o')
        (self.project_root / '.moduleignore').write_text('test_*')
        
        config = {'use_gitignore': False}
        spec = moduleignore.read_ignore_spec(
            self.project_root,
            makefile_config=config
        )
        
        # .gitignore patterns should not be active
        self.assertFalse(spec.match_file('main.o'))
        # .moduleignore patterns should still work
        self.assertTrue(spec.match_file('test_mk.py'))


class TestPathNormalization(unittest.TestCase):
    """Test path normalization for consistent matching."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_normalize_absolute_path(self):
        """Should normalize absolute paths to project-relative."""
        abs_path = self.project_root / 'src' / 'app_mk.py'
        normalized = moduleignore._normalize_path(abs_path, self.project_root)
        
        self.assertEqual('src/app_mk.py', normalized)

    def test_normalize_relative_path(self):
        """Should preserve relative paths with POSIX separators."""
        rel_path = Path('src/app_mk.py')
        normalized = moduleignore._normalize_path(rel_path, self.project_root)
        
        self.assertEqual('src/app_mk.py', normalized)

    def test_normalize_windows_separators(self):
        """Should convert backslashes to forward slashes."""
        # Create a path with backslashes
        win_path = Path('src\\app_mk.py')
        normalized = moduleignore._normalize_path(win_path, self.project_root)
        
        # Should use forward slashes
        self.assertIn('/', normalized)
        self.assertNotIn('\\', normalized)


class TestLegacyCompatibility(unittest.TestCase):
    """Test backward compatibility with old readIgnoreFile API."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_readIgnoreFile_returns_path_list(self):
        """Legacy readIgnoreFile should return list of Path objects."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('app_mk.py\ntest/lib_mk.py')
        
        result = moduleignore.readIgnoreFile(ignore_file)
        
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], Path)
        self.assertEqual('app_mk.py', str(result[0]))

    def test_readIgnoreFile_skips_comments_and_blanks(self):
        """Legacy API should also skip comments and blanks."""
        ignore_file = self.project_root / '.moduleignore'
        ignore_file.write_text('# Comment\n\napp_mk.py\n  # Another comment\ntest/')
        
        result = moduleignore.readIgnoreFile(ignore_file)
        
        self.assertEqual(2, len(result))


if __name__ == '__main__':
    unittest.main()
