import json
from pathlib import Path
from typing import Dict, List

from hoshino.log import new_logger

log = new_logger('ArcadeQueue')

Root: Path = Path(__file__).parent
static: Path = Root / 'static'

arcades_json: Path = static / 'arcades.json'
if not arcades_json.exists():
    arcades_json.write_text("[]")
arcades: List[Dict] = json.load(open(arcades_json, 'r', encoding='utf-8'))

config_json: Path = Root / 'config.json'

SIYUAN: Path = static / 'SourceHanSansSC-Bold.otf'