"""srcs.mk SKIP_PATTERNS emission.

The full srcs.mk writer lives inside pymaketool.main() (argparse + project
settings + addons) and is not unit-testable in isolation. These tests lock the
emission contract at its two ends:

1. A Module carries skip_srcs_patterns / skip_incs_patterns (already prefixed by
   prelib with the module path).
2. The writer emits one `SKIP_PATTERNS += <pat>` line per pattern (srcs + incs
   merged into a single var), and nothing when there are no patterns.

The emit snippet here is kept byte-for-byte identical to the writer block in
src/pymaketool/__init__.py — if the writer changes, this must change with it.
"""

import io
import unittest

from pymakelib.module import Module


def _emit_skip_patterns(mod, buf):
    """Mirror of the SKIP_PATTERNS block in pymaketool.main()'s writer loop."""
    _skips = (getattr(mod, 'skip_srcs_patterns', []) or []) + (getattr(mod, 'skip_incs_patterns', []) or [])
    for pat in dict.fromkeys(_skips):
        buf.write("SKIP_PATTERNS += {}\n".format(pat))


class TestSkipPatternEmission(unittest.TestCase):

    def test_srcs_patterns_emitted_prefixed(self):
        mod = Module(["app/main.c"], [], [], "app/mk.py",
                     skip_srcs_patterns=["app/test*", "app/.template"])
        buf = io.StringIO()
        _emit_skip_patterns(mod, buf)
        self.assertEqual(
            buf.getvalue(),
            "SKIP_PATTERNS += app/test*\nSKIP_PATTERNS += app/.template\n",
        )

    def test_srcs_and_incs_merge_into_one_var(self):
        mod = Module(["app/main.c"], [], [], "app/mk.py",
                     skip_srcs_patterns=["app/test*"],
                     skip_incs_patterns=["app/internal*"])
        buf = io.StringIO()
        _emit_skip_patterns(mod, buf)
        self.assertEqual(
            buf.getvalue(),
            "SKIP_PATTERNS += app/test*\nSKIP_PATTERNS += app/internal*\n",
        )

    def test_duplicates_collapsed(self):
        mod = Module(["app/main.c"], [], [], "app/mk.py",
                     skip_srcs_patterns=["app/test*"],
                     skip_incs_patterns=["app/test*"])
        buf = io.StringIO()
        _emit_skip_patterns(mod, buf)
        self.assertEqual(buf.getvalue(), "SKIP_PATTERNS += app/test*\n")

    def test_no_patterns_emits_nothing(self):
        mod = Module(["app/main.c"], [], [], "app/mk.py")
        buf = io.StringIO()
        _emit_skip_patterns(mod, buf)
        self.assertEqual(buf.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
