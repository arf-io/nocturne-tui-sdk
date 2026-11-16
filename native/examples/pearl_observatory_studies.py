"""Observatory workspaces and controller actions."""
from pathlib import Path
import json
def build_pearl_observatory_studies():
 return json.loads(Path(__file__).with_name('pearl_observatory_studies.json').read_text())
