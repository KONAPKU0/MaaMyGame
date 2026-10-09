"""Unit-test the APK gate with synthetic ZIP fixtures, not Android build outputs."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from verify_apk import verify


class VerifyApkTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assets = self.root / "pi"
        self.files = {
            "interface.json": json.dumps({"task": [{"entry": f"MyTask{i}"} for i in range(1, 4)]}).encode(),
            "resource/pipeline/my_task.json": json.dumps({f"MyTask{i}": {} for i in range(1, 4)}).encode(),
            **{f"resource/model/ocr/{name}": b"synthetic OCR fixture" for name in ("det.onnx", "rec.onnx", "keys.txt")},
        }
        for name, data in self.files.items():
            path = self.assets / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def fixture(self, files=None, native=True, pi=True):
        nested = io.BytesIO()
        with zipfile.ZipFile(nested, "w") as archive:
            for name, data in (self.files if files is None else files).items():
                archive.writestr(name, data)
        path = self.root / "synthetic.apk"
        with zipfile.ZipFile(path, "w") as apk:
            if pi:
                apk.writestr("assets/pi.zip", nested.getvalue())
            if native:
                for name in ("libMaaFramework.so", "libMaaUtils.so", "libMaaAndroidNativeControlUnit.so", "libbridge.so"):
                    apk.writestr(f"lib/arm64-v8a/{name}", b"\x7fELF synthetic native fixture")
        return path

    def test_complete_fixture(self):
        verify(self.fixture(), self.assets)

    def test_missing_and_altered_resources(self):
        for name in self.files:
            with self.subTest(name=name, failure="missing"):
                files = dict(self.files)
                del files[name]
                with self.assertRaises(RuntimeError):
                    verify(self.fixture(files), self.assets)
            with self.subTest(name=name, failure="corrupt"):
                files = {**self.files, name: b"corrupt"}
                with self.assertRaises(RuntimeError):
                    verify(self.fixture(files), self.assets)

    def test_empty_pi_and_missing_native(self):
        with self.assertRaises(RuntimeError):
            verify(self.fixture({}), self.assets)
        with self.assertRaises(KeyError):
            verify(self.fixture(native=False), self.assets)
        with self.assertRaises(KeyError):
            verify(self.fixture(pi=False), self.assets)

    def test_missing_task_even_when_staging_matches(self):
        self.files["interface.json"] = b'{"task": [{"entry": "MyTask1"}]}'
        (self.assets / "interface.json").write_bytes(self.files["interface.json"])
        with self.assertRaises(RuntimeError):
            verify(self.fixture(), self.assets)


if __name__ == "__main__":
    unittest.main()
