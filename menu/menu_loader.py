import json
from datetime import datetime
from menu.cache import MENU_CACHE

def load_menu_from_file(filepath: str):
    """
    Load a menu JSON file (new structure) and push it into MENU_CACHE.

    Expected structure:
    {
        "client_id": "...",
        "franchise_id": "...",
        "locale": "es-CO",
        "version": 1,
        "items": [
            {
                "nombre": "...",
                "variaciones_nombre": [...],
                "ingredientes": [...],
                "precio": 0,
                "modificables": {
                    "eliminables": [...],
                    "agregables": [...],
                    "sustituibles": [...]
                }
            },
            ...
        ]
    }
    """

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            menu_doc = json.load(f)

    except FileNotFoundError:
        raise ValueError(f"Menu JSON file not found: {filepath}")

    # Basic validation
    if "items" not in menu_doc:
        raise ValueError("Invalid menu JSON: missing 'items' field")

    if not isinstance(menu_doc["items"], list):
        raise ValueError("Invalid menu JSON: 'items' must be a list")

    # Store menu in cache
    MENU_CACHE["menu"] = menu_doc["items"]
    MENU_CACHE["client_id"] = menu_doc.get("client_id")
    MENU_CACHE["franchise_id"] = menu_doc.get("franchise_id")
    MENU_CACHE["locale"] = menu_doc.get("locale", "es-CO")
    MENU_CACHE["loaded_at"] = datetime.utcnow()
    MENU_CACHE["version"] = menu_doc.get("version", 1)

    print(f"[INFO] Menu loaded from file: {filepath} (version={MENU_CACHE['version']})")

    return MENU_CACHE["menu"]

