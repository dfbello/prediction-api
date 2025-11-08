from flask import Flask, jsonify, request
import speech_recognition as sr
import unicodedata
from model import predict_text
from model.postprocessing import postprocess_entities_to_json
from model.menu_items import MENU_ITEMS

app = Flask(__name__)

def normalize_accents(text):
	#Convert accented chars to canonical form (e.g: ú -> u)
	text = unicodedata.normalize("NFD", text)
	text = "".join(c for c in text if unicodedata.category(c) != "Mn")
	return text

@app.route("/predict", methods=["GET"])
def predict_order():
	"""
	Expects JSON: {"audio_path": "audio_samples/voice1.wav"}
	"""
	data = request.get_json()
	audio_path = data.get("audio_path")
	if not audio_path:
		return jsonify({"error": "audio_path not provided"}), 400

	recognizer = sr.Recognizer()
	try:
		with sr.AudioFile(audio_path) as source:
			audio = recognizer.record(source)
			text = recognizer.recognize_google(audio, language="es-CO")

	except Exception as e:
		return jsonify({"error": f"Speech recognition failed: {str(e)}"}), 500

	text = normalize_accents(text)
	entities = predict_text(text)
	print(text)
	order_json = postprocess_entities_to_json(text, entities, MENU_ITEMS)

	return jsonify({
		"transcript": text,
		"order_prediction": order_json
	})

if __name__ == "__main__":
	app.run(debug=True)
