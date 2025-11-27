from menu.cache import MENU_CACHE

## TO CHANGE UNTIL MENU IS RECEIVED THROUGH ENDPOINT
"""
def set_menu(menu):
    MENU_CACHE["menu"] = menu
    print("[INFO] Active menu updated.")
"""

def get_menu():
    """Read the active menu used by the predictor."""
    return MENU_CACHE.get("menu")

