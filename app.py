from flask import Flask, jsonify, request
import speech_recognition as sr
import os

from config import CLIENT_ID, FRANCHISE_ID
from model.loader import find_latest_model, load_model
from menu.menu_loader import load_menu_from_file
from menu.manager import set_menu
from prediction.predictor import predict


app = Flask(__name__)

RECORDINGS_DIR = "audio_samples"
MODELS_BASE_DIR = "models/test_client_test_store"
MODEL_SLOT_1 = os.path.join(MODELS_BASE_DIR, "nlu_model_1")
MODEL_SLOT_2 = os.path.join(MODELS_BASE_DIR, "nlu_model_2")

active_slot = 1
model_path = None
ner_pipeline = None
load_menu_from_file("../menu_items.json")

# Intenta cargar el modelo al inicio, pero continúa si falla
try:
    model_path = find_latest_model(MODEL_SLOT_1) if active_slot == 1 else find_latest_model(MODEL_SLOT_2)
    ner_pipeline = load_model(model_path)
except Exception as e:
    print(f"[WARNING] Could not load model at startup: {str(e)}")
    model_path = None
    ner_pipeline = None


@app.route("/predict", methods=["GET"])
def predict_order():

    # ---------------------------------
    # GET JSON REQUEST DATA
    # ---------------------------------

    if not model_path:
        return jsonify({"error": "Model path not set"}), 503


    """
    Expects JSON: {"filename": "voice1.wav"}
    """
    if not request.is_json:
        return jsonify({"error": "Expected JSON payload"}), 400

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "filename not provided"}), 400

    # Prevent directory traversal attacks like "../../etc/passwd"
    if "/" in filename or "\\" in filename:
        return jsonify({"error": "Invalid filename"}), 400

    audio_path = os.path.join(RECORDINGS_DIR, filename)


    if not os.path.exists(audio_path):
        return jsonify({"error": f"Audio file not found: {filename}"}), 404

    if os.path.getsize(audio_path) < 500: # ~0.5 KB
        return jsonify({"error": f"Audio file ({filename}) is empty or too short"})

    # ---------------------------------
    # STT API REQUEST AND RESPONSE
    # ---------------------------------

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="es-CO")

    except Exception as e:
        return jsonify({"error": f"Speech recognition failed: {str(e)}"}), 500

    # ---------------------------------
    # TRANSFORMER MODEL & POSTPROCESSING AND FINAL OUTPUT
    # ---------------------------------
    result = predict(text, ner_pipeline)
    if result:
        return jsonify(result)
    else:
        return jsonify({"error": "Prediction failed: No structured items found"}), 400

@app.route("/menu/update", methods=["POST"])
def menu_update():
    """
    Webhook endpoint called by the Menu Management Service.
    Receives a full menu object and replaces the cached menu.
    """
    global model_path, ner_pipeline, active_slot
    
    if not request.is_json:
        return jsonify({"error": "Expected JSON body"}), 400

    data = request.get_json()

    menu = data.get("menu")
    if menu is None:
        return jsonify({"error": "Missing 'menu' field"}), 400

    ## Validate client and franchise
    print(f"Client ID received: {menu.get('client_id')}")

    if menu.get("client_id") != CLIENT_ID:
        return jsonify({"error": f"Field \"client_id\" does not match current client id"}), 400

    if menu.get("franchise_id") != FRANCHISE_ID:
        return jsonify({"error": "Field \"franchise_id\" does not match current franchise id"}), 400

    # Replace the menu in cache for the predictor
    set_menu(menu)

    # 🔁 swap slot (blue/green)
    active_slot = 2 if active_slot == 1 else 1
    next_model_dir = MODEL_SLOT_1 if active_slot == 1 else MODEL_SLOT_2

    print(f"[INFO] Swapping to nlu_model_{active_slot}")

    try:
        model_path = find_latest_model(next_model_dir)
        ner_pipeline = load_model(model_path)
        print(f"[INFO] Model loaded from {model_path}")
        return jsonify({
            "status": "menu updated",
            "active_slot": active_slot,
            "model_path": model_path
        }), 200

    except Exception as e:
        print(f"[ERROR] Failed to load model from slot {active_slot}: {str(e)}")
        return jsonify({
            "error": "Failed to load model",
            "slot": active_slot,
            "details": str(e)
        }), 500
    

if __name__ == "__main__":
    app.run(debug=True)
