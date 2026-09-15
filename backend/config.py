"""Central configuration for filesystem layout and local runtime limits."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SAMPLE_VIDEO = DATA_DIR / "sample.mp4"
MODEL_DIR = ROOT / "models"
MAX_UPLOAD_BYTES = 2 * 1024**3
MAX_VIDEO_SECONDS = 10_800
