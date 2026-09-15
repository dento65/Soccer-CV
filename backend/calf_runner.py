"""Adapter for SoccerNet's official CALF external-video inference release."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALF = ROOT / "third_party" / "sn-spotting" / "Benchmarks" / "CALF"
PYTHON = ROOT / ".venv" / "bin" / "python"
if not PYTHON.exists():
    PYTHON = Path(sys.executable)
CHECKPOINT = CALF / "models" / "CALF_benchmark" / "model.pth.tar"


def available() -> tuple[bool, str]:
    if not CHECKPOINT.exists():
        return False, "Official CALF checkpoint is missing"
    if not PYTHON.exists():
        return False, "Project Python environment is missing"
    try:
        subprocess.run([str(PYTHON), "-c", "import torch, tensorflow, cv2, SoccerNet"], check=True, capture_output=True, timeout=20)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False, "CALF runtime dependencies are still installing"
    return True, "Official SoccerNet CALF checkpoint ready"


def infer(video: Path, destination: Path) -> list[dict]:
    ok, message = available()
    if not ok:
        raise RuntimeError(message)
    work = destination / "calf"
    work.mkdir(parents=True, exist_ok=True)
    # The upstream inference writes fixed paths. Isolate one inference at a time
    # by running inside its release directory and moving the final artifact.
    output_dir = CALF / "inference" / "outputs"
    # The released CALF script writes temporary video/features here. Create it
    # on fresh Docker/Git checkouts before launching FFmpeg.
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "Predictions-v2.json"
    output.unlink(missing_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CALF.parent.parent.parent) + os.pathsep + env.get("PYTHONPATH", "")
    command = [str(PYTHON), "inference/main.py", "--video_path", str(video), "--model_name", "CALF_benchmark"]
    result = subprocess.run(command, cwd=CALF, env=env, capture_output=True, text=True, timeout=7200)
    (work / "calf.log").write_text((result.stdout or "") + "\n" + (result.stderr or ""))
    if result.returncode != 0:
        raise RuntimeError(f"CALF inference failed. See {work / 'calf.log'}")
    if not output.exists():
        raise RuntimeError("CALF finished without Predictions-v2.json")
    shutil.copy2(output, work / "Predictions-v2.json")
    payload = json.loads(output.read_text())
    events = []
    for index, item in enumerate(payload.get("predictions", [])):
        events.append({
            "event_id": f"calf-{index}",
            "class_id": item["label"].lower().replace(" ", "_").replace("->", "_to_"),
            "label": item["label"],
            "timestamp_sec": int(item["position"]) / 1000,
            "confidence": float(item["confidence"]),
            "model": "SoccerNet CALF benchmark",
        })
    return events
