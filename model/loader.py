
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

MODEL_PATH = "model/nlu_model/checkpoint-300"   # adjust if needed

_nlu_pipeline = None

def load_model():
    """
    Loads the HuggingFace NER model and pipeline only once.
    Returns the global pipeline object.
    """
    global _nlu_pipeline

    if _nlu_pipeline is not None:
        return _nlu_pipeline

    print("[INFO] Loading NLU model...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

    _nlu_pipeline = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="first"
    )

    print("[INFO] NLU model loaded successfully.")
    return _nlu_pipeline