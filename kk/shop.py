from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from .data_store import load_shop

def get_item(shop: Dict, category: str, item_id: str) -> Optional[Dict]:
    return shop.get(category, {}).get(item_id)

def list_item_ids(shop: Dict, category: str) -> List[str]:
    return list(shop.get(category, {}).keys())

def group_items(shop: Dict, category: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """Return items grouped by their 'group' metadata.
    Returns mapping group_name -> list[(item_id, item_dict)]
    """
    grouped = defaultdict(list)
    for iid, item in shop.get(category, {}).items():
        grp = item.get("group", "Allgemein")
        grouped[grp].append((iid, item))
    # sort for stable UI
    for g in grouped:
        grouped[g].sort(key=lambda pair: pair[1].get("name", pair[0]).lower())
    return dict(sorted(grouped.items(), key=lambda kv: kv[0].lower()))
