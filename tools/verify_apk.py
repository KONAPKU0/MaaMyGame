"""Check the built APK, including every byte of the staged PI and OCR files."""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(apk_path, assets):
    with zipfile.ZipFile(apk_path) as apk:
        with zipfile.ZipFile(io.BytesIO(apk.read("assets/pi.zip"))) as pi:
            expected = {p.relative_to(assets).as_posix(): p for p in assets.rglob("*") if p.is_file()}
            if not expected:
                raise RuntimeError("Empty staged PI")
            actual = {p.filename for p in pi.infolist() if not p.is_dir()}
            if actual != set(expected):
                raise RuntimeError(f"PI file mismatch: missing={set(expected) - actual}, extra={actual - set(expected)}")
            for name, path in expected.items():
                if hashlib.sha256(pi.read(name)).digest() != hashlib.sha256(path.read_bytes()).digest():
                    raise RuntimeError(f"PI content mismatch: {name}")
            interface = json.loads(pi.read("interface.json"))
            pipeline = json.loads(pi.read("resource/pipeline/my_task.json"))
            entries = {t["entry"] for t in interface["task"]}
            if entries != {"MyTask1", "MyTask2", "MyTask3"} or not entries <= pipeline.keys():
                raise RuntimeError("Missing template tasks")
            for name in ("det.onnx", "rec.onnx", "keys.txt"):
                if not pi.read(f"resource/model/ocr/{name}"):
                    raise RuntimeError(f"Empty OCR model: {name}")
        for name in ("libMaaFramework.so", "libMaaUtils.so", "libMaaAndroidNativeControlUnit.so", "libbridge.so"):
            if not apk.read(f"lib/arm64-v8a/{name}").startswith(b"\x7fELF"):
                raise RuntimeError(f"Missing/invalid Android native library: {name}")
    print(f"Verified {apk_path}: {len(expected)} exact PI files, three template tasks, OCR and arm64 native libraries")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("apk", type=Path)
    parser.add_argument("--assets", type=Path, default=ROOT / "build/android-pi")
    args = parser.parse_args()
    try:
        verify(args.apk, args.assets)
    except Exception as error:
        message = str(error).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::error title=APK resource verification failed::{message}', flush=True)
        raise


if __name__ == "__main__":
    main()
