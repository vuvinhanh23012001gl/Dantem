from pathlib import Path
from typing import Any, Dict
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def load_settings(config_path: Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load YAML settings for the OCR & Orientation application."""
    if not config_path.exists():
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
