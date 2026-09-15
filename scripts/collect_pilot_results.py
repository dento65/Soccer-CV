"""Write a small, auditable pilot-run table; this is not an accuracy benchmark."""
import json
from pathlib import Path
from backend.config import DATA_DIR
from backend.services.experiments import collect_pilot_rows

out=Path('experiments/pilot_runs.json'); out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({'purpose':'Runtime and pipeline sanity checks, not labelled accuracy evaluation','runs':collect_pilot_rows(DATA_DIR)},indent=2))
print(out)
