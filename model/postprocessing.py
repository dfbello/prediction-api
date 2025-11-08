from fuzzywuzzy import process

def postprocess_entities_to_json(text, entities, menu_items, similarity_threshold=80):
    """
    Convert model predictions (entities) into a structured restaurant order JSON.
    """
    entities.sort(key=lambda x: x["start"])
    items, current_item, global_mods = [], None, []

    num_words = {
        "un": 1, "una": 1, "unas": 1, "unos": 1, "dos": 2, "tres": 3, "cuatro": 4,
        "cinco": 5, "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
        "diez": 10, "once": 11, "doce": 12, "trece": 13
    }

    def best_match(txt):
        match, score = process.extractOne(txt, menu_items)
        return match if score >= similarity_threshold else txt

    for e in entities:
        label = e["entity_group"]
        word = e["word"].replace("##", "").strip()

        if label == "NUM":
            if current_item:
                items.append(current_item)
            cantidad = num_words.get(word.lower(), word)
            try:
                cantidad = int(cantidad)
            except ValueError:
                pass
            current_item = {"cantidad": cantidad, "producto": "", "modificadores": []}

        elif label == "ITEM":
            prod = best_match(word)
            if not current_item:
                current_item = {"cantidad": 1, "producto": prod, "modificadores": []}
            elif not current_item["producto"]:
                current_item["producto"] = prod
            else:
                items.append(current_item)
                current_item = {"cantidad": 1, "producto": prod, "modificadores": []}

        elif label == "MODIFICADOR":
            (current_item["modificadores"] if current_item else global_mods).append(word)

    if current_item:
        items.append(current_item)
    for item in items:
        item["modificadores"].extend(global_mods)

    return {"items": items}
