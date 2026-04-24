import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime_paths import runtime_path, sanitize_name


class RuntimePathsTest(unittest.TestCase):
    def test_sanitize_name_normalizes_unsafe_values(self):
        self.assertEqual(sanitize_name(" ../weird name!! "), "weird-name")
        self.assertEqual(sanitize_name(""), "default")

    def test_runtime_path_uses_override_dir_and_sanitized_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict("os.environ", {"BU_RUNTIME_DIR": tmpdir, "BU_NAME": "../odd name"}, clear=False):
                path = runtime_path("sock")
                self.assertEqual(path, Path(tmpdir) / "bu-odd-name.sock")


if __name__ == "__main__":
    unittest.main()
