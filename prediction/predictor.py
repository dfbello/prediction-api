# prediction/predictor.py

from prediction.text_cleaner import normalize_text
from model.postprocessing import postprocess_entities_to_json
from menu.manager import get_menu

def predict(text: str, ner_pipeline):

    menu = get_menu()

    if menu is None:
        return {"error": "No menu loaded"}
    clean_text = normalize_text(text)

    entities = ner_pipeline(clean_text)

    final_output = postprocess_entities_to_json(clean_text, entities, menu)

    if final_output:
        return {
            "transcript": clean_text,
            "prediction": final_output,
        }
    else:
        return final_output
    
