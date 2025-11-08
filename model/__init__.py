from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification

# Load model only once when Flask starts
MODEL_PATH = "model/nlu_model/checkpoint-300"  # relative to project root

print("[INFO] Loading NLU model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForTokenClassification.from_pretrained(MODEL_PATH)

ner_pipeline = pipeline(
    "ner",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="first"
)

print("[INFO] NLU model loaded successfully.")

# Utility for inference
def predict_text(text: str):
    """
    Runs NER prediction on a given text and returns the raw entities.
    """
    return ner_pipeline(text)
