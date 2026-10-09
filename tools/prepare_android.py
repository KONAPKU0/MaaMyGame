"""Stage the existing pure Pipeline examples without modifying source resources."""
import json
import shutil
from pathlib import Path

import jsonc

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = {"MyTask1", "MyTask2", "MyTask3"}


def main():
    source = ROOT / "assets"
    output = ROOT / "build/android-pi"
    for name in ("det.onnx", "rec.onnx", "keys.txt"):
        path = source / "resource/model/ocr" / name
        if not path.is_file() or not path.stat().st_size:
            raise RuntimeError(f"Missing OCR resource: {path}; run tools/configure.py")
    interface = jsonc.loads((source / "interface.json").read_text(encoding="utf-8"))
    if interface.get("agent"):
        raise RuntimeError("This Pipeline-only APK profile does not bundle an Agent runtime")
    interface["name"] = "MaaMyGame"
    interface["github"] = "https://github.com/KONAPKU0/MaaMyGame"
    interface["controller"] = [c for c in interface["controller"] if c["type"] == "Adb"]
    interface["task"] = [t for t in interface["task"] if t["entry"] in ENTRIES]
    if not interface["controller"] or {t["entry"] for t in interface["task"]} != ENTRIES:
        raise RuntimeError("Expected Adb controller and all three template Pipeline tasks")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    # Gradle Sync uses Ant's default excludes, including version-control files.
    # Keep the staging tree identical to the files intended to ship in pi.zip.
    shutil.copytree(source / "resource", output / "resource", ignore=shutil.ignore_patterns("__pycache__", ".gitignore", ".gitattributes", ".git"))
    shutil.copy2(ROOT / "LICENSE", output / "LICENSE")
    (output / "interface.json").write_text(json.dumps(interface, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    print(f"Staged {len(interface['task'])} template tasks and OCR at {output}")


if __name__ == "__main__":
    main()
