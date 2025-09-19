from typing import Dict, List, Optional
from PIL import Image

from .config import LAYERING_ORDER

def _composite(base: Optional[Image.Image], layer: Image.Image) -> Image.Image:
    if base is None:
        return layer.copy()
    if layer.size != base.size:
        layer = layer.resize(base.size)
    base.alpha_composite(layer)
    return base

def _open_rgba(path: str) -> Optional[Image.Image]:
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None

def render_katzenklo(equipped: Dict[str, List[str]], litter_state: str, occupied: bool|str, shop_data: Dict) -> Optional[Image.Image]:
    base: Optional[Image.Image] = None

    for category in LAYERING_ORDER:
        for item_id in equipped.get(category, []):
            item = shop_data.get(category, {}).get(item_id)
            if not item:
                continue

            if category == "Katzenstreu":
                # Draw layered litter depending on state
                for state in ["clean", "piss", "poop"]:
                    if state != "clean" and state not in litter_state:
                        continue
                    img_path = item.get("image", "").replace("clean.png", f"{state}.png")
                    img = _open_rgba(img_path)
                    if img:
                        base = _composite(base, img)
            else:
                img = _open_rgba(item.get("image", ""))
                if img:
                    base = _composite(base, img)
    
    # print(occupied)
    if occupied:
        img_path = f"img/cats/{occupied.lower()}.png"
        # print(img_path)
        img = _open_rgba(img_path)
        if img:
            # print(1)
            base = _composite(base, img)

    return base
