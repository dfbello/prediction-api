from datetime import datetime
from cache import MENU_CACHE
import json

from pathlib import Path
MENU_ITEMS = (Path(__file__).resolve().parents[2] / "menu_items.json")

def set_menu(menu_doc):

	# Basic validation
	if "items" not in menu_doc:
		raise ValueError("Invalid menu JSON: missing 'items' field")

	if not isinstance(menu_doc["items"], list):
		raise ValueError("Invalid menu JSON: 'items' must be a list")
	
	# Persist posted menu to disk
	try:
		with open(MENU_ITEMS, "w", encoding="utf-8") as f:
			json.dump(menu_doc, f, ensure_ascii=False, indent=4)
		print(f"[INFO] Active menu written to disk at {MENU_ITEMS}")
	except Exception as e:
		print(f"[ERROR] Failed to write menu file {MENU_ITEMS}: {e}")

	# Store menu in cache
	MENU_CACHE["menu"] = menu_doc["items"]
	MENU_CACHE["client_id"] = menu_doc.get("client_id")
	MENU_CACHE["franchise_id"] = menu_doc.get("franchise_id")
	MENU_CACHE["locale"] = menu_doc.get("locale", "es-CO")
	MENU_CACHE["loaded_at"] = datetime.now(datetime.timezone.utc)
	MENU_CACHE["version"] = menu_doc.get("version", 1)

	print("[INFO] Active menu updated.")


def get_menu():
	"""Read the active menu used by the predictor."""
	return MENU_CACHE.get("menu")

