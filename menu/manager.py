from datetime import datetime
from menu.cache import MENU_CACHE

def set_menu(menu_doc):

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

	print("[INFO] Active menu updated.")


def get_menu():
	"""Read the active menu used by the predictor."""
	return MENU_CACHE.get("menu")

