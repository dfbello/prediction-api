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
MODELS_DIR = "model/nlu_model/"

model_path = find_latest_model(MODELS_DIR)
ner_pipeline = load_model(model_path)
load_menu_from_file("../menu_items.json")


@app.route("/predict", methods=["GET"])
def predict_order():

	# ---------------------------------
	# GET JSON REQUEST DATA
	# ---------------------------------

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
	return jsonify(result)

@app.route("/menu/update", methods=["POST"])
def menu_update():
	"""
	Webhook endpoint called by the Menu Management Service.
	Receives a full menu object and replaces the cached menu.
	"""
	if not request.is_json:
		return jsonify({"error": "Expected JSON body"}), 400

	data = request.get_json()

	menu = data.get("menu")
	if menu is None:
		return jsonify({"error": "Missing 'menu' field"}), 400

	## Validate client and franchise

	if menu.get("client_id") != CLIENT_ID:
		return jsonify({"error": "Field \"client_id\" does not match current client id"}), 400

	if menu.get("franchise_id") != FRANCHISE_ID:
		return jsonify({"error": "Field \"franchise_id\" does not match current franchise id"}), 400

	# Replace the menu in cache for the predictor
	set_menu(menu)

	print("[INFO] Menu updated successfully via webhook")
	return jsonify({"status": "menu updated"}), 200


if __name__ == "__main__":
	app.run(debug=True)
