"""Current production scope metadata, separate from city origin geography."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
def config():
 p=ROOT/'output/plano_city/active_scope.json'
 return json.loads(p.read_text()) if p.exists() else json.loads((ROOT/'config/routing_scope.json').read_text())
def buffer_m():return int(config()['routing_buffer_m'])
