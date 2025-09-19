import json
from typing import Any, Dict
from .config import SHOP_FILE, STATS_FILE, CATS_FILE

def _load_json(path: str, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default

def _save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_shop() -> Dict:
    """Flat ID-based shop structure by category.

    Example:

    {
  "Katzenklos": {
      "box_std_red": {"name": "...", "group": "Standard", "price": 5, "image": "..."}
  }
}

    """
    return _load_json(SHOP_FILE, {})

def load_stats() -> Dict:
    return _load_json(STATS_FILE, {})

def save_stats(data: Dict) -> None:
    _save_json(STATS_FILE, data)

def load_cats() -> Dict:
    return _load_json(CATS_FILE, {})
