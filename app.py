from flask import Flask, jsonify, request
import speech_recognition as sr
import unicodedata
import os
from model import predict_text
from model.postprocessing import postprocess_entities_to_json
from model.menu_items import MENU_ITEMS

app = Flask(__name__)


RECORDINGS_DIR = "audio_samples"

def normalize_accents(text):
	#Convert accented chars to canonical form (e.g: ú -> u)
	text = unicodedata.normalize("NFD", text)
	text = "".join(c for c in text if unicodedata.category(c) != "Mn")
	return text

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


	if not os.path.exist(audio_path):
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

	text = normalize_accents(text)

	# ---------------------------------
	# TRANSFORMER MODEL
	# ---------------------------------
	entities = predict_text(text)


	# ---------------------------------
	# POSTPROCESSING AND FINAL OUTPUT
	# ---------------------------------
	order_json = postprocess_entities_to_json(text, entities, MENU_ITEMS)

	return jsonify({
		"transcript": text,
		"order_prediction": order_json
	})

if __name__ == "__main__":
	app.run(debug=True)
