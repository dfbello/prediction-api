import os
import glob
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

_nlu_pipeline = None


def find_latest_model(base_dir):
    """
    Returns the path (base_dir + filename) of the latest modified checkpoint-* folder on base_dir
    """
    # Find all folders "checkpoint-*"
    checkpoints = glob.glob(os.path.join(base_dir, "checkpoint-*"))

    if not checkpoints:
        raise RuntimeError(f"No checkpoints found in {base_dir}")

    # Pick the newest folder by modification time
    latest = max(checkpoints, key=os.path.getmtime)
    print(f"[INFO] Latest checkpoint detected: {latest}")

    return latest



def load_model(model_path):
    """
    Loads the HuggingFace NER model and pipeline only once.
    Returns the global pipeline object.
    """
    global _nlu_pipeline

    if _nlu_pipeline is not None:
        return _nlu_pipeline

    print("[INFO] Loading NLU model...")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForTokenClassification.from_pretrained(model_path)

    _nlu_pipeline = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="first"
    )

    print("[INFO] NLU model loaded successfully.")
    return _nlu_pipeline
