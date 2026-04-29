import unicodedata
from fuzzywuzzy import process, fuzz
from prediction.text_cleaner import normalize_text


def postprocess_entities_to_json(text, entities, menu_items, similarity_threshold=80):
    """
    Convert model predictions into the legacy structured order:

    {
        "items": [
            {
                "cantidad": <int>,
                "producto": <string>,
                "modificadores": [...]
            }
        ]
    }

    menu_items: list of dictionaries with structure:
      {
        "name": "...",
        "aliases": [...],
        "ingredients": [...],
        "price": ...,
        "modifiers": {...}
      }
    """

    # ------------------------------------------------------------
    # 1. Build lookup tables for fuzzy alias matching
    # ------------------------------------------------------------

    alias_lookup = {}  # normalized_alias \u2192 item_dict
    alias_list = []    # all normalized aliases

    for item in menu_items:
        primary = normalize_text(item["name"])
        alias_lookup[primary] = item
        alias_list.append(primary)

        for alias in item.get("aliases", []):
            a_norm = normalize_text(alias)
            alias_lookup[a_norm] = item
            alias_list.append(a_norm)

    alias_list = list(set(alias_list))  # dedupe

    # ------------------------------------------------------------
    # 2. Fuzzy match resolver
    # ------------------------------------------------------------

    def resolve_item_name(raw_word: str) -> str:
        """Return the *menu item name* (string), NOT the full dict."""
        raw_norm = normalize_text(raw_word)

        # Reject very short tokens unless they match an alias token exactly
        if len(raw_norm) <= 2:
            for alias in alias_list:
                # alias already normalized; check whole-token equality, not substring
                if raw_norm in alias.split():
                    return alias_lookup[alias]["name"]
            return None

        # Fast exact lookup
        if raw_norm in alias_lookup:
            return alias_lookup[raw_norm]["name"]

        # Use token_set_ratio to compare normalized strings (better for multiword aliases)
        match, score = process.extractOne(raw_norm, alias_list, scorer=fuzz.token_set_ratio)
        print(f"[DEBUG] Fuzzy match: '{raw_word}' -> '{match}' (score: {score})")

        # Special-case short inputs: require very high confidence
        if len(raw_norm) < 4 and score < 90:
            return None

        if score >= similarity_threshold:
            return alias_lookup[match]["name"]

        return None

    # ------------------------------------------------------------
    # 3. Order building
    # ------------------------------------------------------------

    entities.sort(key=lambda x: x["start"])
    items = []
    current_item = None
    global_mods = []

    num_words = {
        "un": 1, "una": 1, "uno": 1,
        "unos": 1, "unas": 1,
        "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
        "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
        "diez": 10, "once": 11, "doce": 12, "trece": 13
    }

    # ------------------------------------------------------------
    # 4. Main entity loop
    # ------------------------------------------------------------

    for ent in entities:
        label = ent["entity_group"]
        word = ent["word"].replace("##", "").strip()

        # -------------------------------
        # QUANTITY
        # -------------------------------
        if label == "NUM":
            if current_item:
                items.append(current_item)

            qty = num_words.get(word.lower(), word)
            try:
                qty = int(qty)
            except:
                pass

            current_item = {
                "cantidad": qty,
                "producto": None,
                "modificadores": []
            }

        # -------------------------------
        # ITEM
        # -------------------------------
        elif label == "ITEM":
            resolved_name = resolve_item_name(word)
            
            if resolved_name is None:
                continue  # skip unrecognized items

            if not current_item:
                # e.g., user said "hamburguesa" with no number
                current_item = {
                    "cantidad": 1,
                    "producto": resolved_name,
                    "modificadores": []
                }
            else:
                
                if current_item["producto"] is None:
                    current_item["producto"] = resolved_name
                else:
                    # new item begins
                    items.append(current_item)
                    current_item = {
                        "cantidad": 1,
                        "producto": resolved_name,
                        "modificadores": []
                    }

        # -------------------------------
        # MODIFIER
        # -------------------------------
        elif label == "MODIFICADOR":
            (current_item["modificadores"] if current_item else global_mods).append(word)

    # ------------------------------------------------------------
    # 5. Finalization
    # ------------------------------------------------------------

    if current_item:
        items.append(current_item) if current_item["producto"] else None

    #for it in items:
    #    it["modificadores"].extend(global_mods)

    return {"items": items} if items else None

