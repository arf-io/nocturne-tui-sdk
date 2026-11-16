"""Pearl instruments, scene configuration and controller actions.
"""
import json
from pathlib import Path
def build_pearl_data_studies():
 return json.loads(Path(__file__).with_name('pearl_data_studies.json').read_text())
