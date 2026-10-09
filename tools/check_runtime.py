"""Load the actual resource and OCR models with the native MaaFramework library."""
import argparse
import json
from pathlib import Path

from maa.resource import Resource
from maa.toolkit import Toolkit

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=ROOT / "build/android-pi")
    args = parser.parse_args()
    log_dir = ROOT / "build/runtime-check"
    log_dir.mkdir(parents=True, exist_ok=True)
    Toolkit.init_option(log_dir)
    resource = Resource()
    job = resource.post_bundle(args.assets / "resource").wait()
    if not job.succeeded or not resource.loaded:
        raise RuntimeError(f"Native resource/OCR load failed: {job.status}")
    interface = json.loads((args.assets / "interface.json").read_text(encoding="utf-8"))
    for task in interface["task"]:
        if task["entry"] not in resource.node_list:
            raise RuntimeError(f"Missing task entry: {task['entry']}")
    print(f"Native resource/OCR load passed; {len(interface['task'])} task entries present, {len(resource.node_list)} nodes")


if __name__ == "__main__":
    main()
