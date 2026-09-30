# Prediction API

An API that accepts a local audio file, transcribes it with Google Speech-to-Text, and predicts the order from a restaurant menu using a Hugging Face token-classification model.

The project is built as a small Flask service that:

- receives a request containing a filename pointing to an audio sample,
- converts speech to text in Spanish (`es-CO`),
- runs an NLU/NER model against the transcript,
- matches extracted entities against the active menu,
- returns a structured JSON order payload.

## Project overview

This repository is a prototype for voice-order prediction. The service expects an audio file recorded locally, identifies spoken items and modifiers, and resolves them to menu entries using fuzzy matching and a cached menu document.

The main flow is:

1. A client sends a JSON payload with a filename to `/predict`.
2. The Flask app verifies that the file exists and is non-empty.
3. `SpeechRecognition` loads the audio and calls Google STT.
4. The transcript is cleaned and passed to a Hugging Face NER pipeline.
5. `model/postprocessing.py` converts entity predictions into a structured order object.
6. The result is returned as JSON.

## Architecture

### 1. Flask application entry point

File: `app.py`

This is the API server. It exposes two routes:

- `GET /predict`
  - Reads `filename` from the JSON body.
  - Verifies the file exists in `audio_samples/`.
  - Runs speech recognition.
  - Calls the prediction pipeline.
  - Returns a JSON response.

- `POST /menu/update`
  - Accepts a full menu document from a Menu Management Service.
  - Validates `client_id` and `franchise_id` against `config.py`.
  - Stores the new menu in memory and on disk.
  - Swaps the active model slot (`nlu_model_1` / `nlu_model_2`) and reloads the model.

The app also loads a menu during startup and attempts to load the latest model checkpoint from the active slot.

### 2. Configuration

File: `config.py`

Contains the active client and franchise identifiers used to validate incoming menu updates:

```python
CLIENT_ID = "test_client"
FRANCHISE_ID = "test_store"
```

These values are used to reject menu updates that do not match the configured tenant.

### 3. Menu layer

Directory: `menu/`

Responsible for menu lifecycle and cache management:

- `menu/cache.py` — in-memory cache for the current menu
- `menu/manager.py` — validates, writes, and exposes the current menu
- `menu/menu_loader.py` — loads menu JSON files from disk into the cache

The active menu is stored in the `MENU_CACHE` dictionary and also persisted to `menu_items.json` at the project root.

### 4. Prediction layer

Directory: `prediction/`

- `prediction/text_cleaner.py` — normalizes transcript text before model inference
- `prediction/predictor.py` — orchestrates the full prediction flow

The predictor loads the current menu, normalizes the transcript, sends it to the loaded NER pipeline, and then converts recognized entities into a structured order object.

### 5. Model loading and postprocessing

Directory: `model/`

- `model/loader.py` — finds the newest checkpoint folder in a model slot and loads the Hugging Face pipeline
- `model/postprocessing.py` — transforms recognized entities into a JSON order payload, using fuzzy matching against menu aliases

The model loader looks for checkpoint folders matching this pattern:

```text
models/test_client_test_store/<slot>/checkpoint-* 
```

and chooses the newest checkpoint by modification time.

### 6. Helper scripts

Directory: `bin/`

- `bin/record-order` — shell script that records audio samples, likely for capturing test-order clips to validate the model and API.

## Data flow

```text
Client request
  -> Flask route (/predict)
  -> validate audio file
  -> SpeechRecognition -> transcript
  -> clean text
  -> Hugging Face NER model
  -> postprocess entities to JSON
  -> return prediction
```

## Expected request format

### Predict endpoint

```http
GET /predict
Content-Type: application/json
```

Body:

```json
{
  "filename": "order_01.wav"
}
```

The file must exist under `audio_samples/` and should not contain path traversal segments like `../`.

Example response:

```json
{
  "transcript": "dos hamburguesas con queso",
  "prediction": {
    "items": [
      {
        "cantidad": 2,
        "producto": "Hamburguesa",
        "modificadores": ["con queso"]
      }
    ]
  }
}
```

### Menu update endpoint

```http
POST /menu/update
Content-Type: application/json
```

Body:

```json
{
  "menu": {
    "client_id": "test_client",
    "franchise_id": "test_store",
    "locale": "es-CO",
    "version": 1,
    "items": [
      {
        "name": "Hamburguesa",
        "aliases": ["hamburguesa", "burger"],
        "ingredients": [],
        "price": 0,
        "modifiers": {
          "eliminables": [],
          "agregables": [],
          "sustituibles": []
        }
      }
    ]
  }
}
```

## Setup instructions

### Prerequisites

- Python 3.10+
- pip
- A working internet connection for downloading Python dependencies and Hugging Face model files
- A local directory named `audio_samples/` for test audio files
- A trained model checkpoint under the expected model path structure

### 1. Clone the repository

```bash
git clone https://github.com/dfbello/prediction-api.git
cd prediction-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare the required folders and files

Create the audio directory:

```bash
mkdir -p audio_samples
```

Create a model directory matching the expected layout:

```bash
mkdir -p models/test_client_test_store/nlu_model_1
mkdir -p models/test_client_test_store/nlu_model_2
```

Place a trained Hugging Face NER model checkpoint inside one of those directories, for example:

```text
models/test_client_test_store/nlu_model_1/checkpoint-1234/
```

The app will select the newest `checkpoint-*` folder automatically.

Create a menu file at the project root named `menu_items.json` with a structure like:

```json
{
  "client_id": "test_client",
  "franchise_id": "test_store",
  "locale": "es-CO",
  "version": 1,
  "items": [
    {
      "name": "Hamburguesa",
      "aliases": ["hamburguesa", "burger"],
      "ingredients": [],
      "price": 0,
      "modifiers": {
        "eliminables": [],
        "agregables": [],
        "sustituibles": []
      }
    }
  ]
}
```

### 5. Run the API

```bash
python app.py
```

The Flask app will start in development mode by default:

```text
http://127.0.0.1:5000
```

## Example workflow

### Start the service

```bash
python app.py
```

### Send a sample prediction request

```bash
curl -X GET http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"filename":"sample_order.wav"}'
```

### Update the menu and reload the model

```bash
curl -X POST http://localhost:5000/menu/update \
  -H "Content-Type: application/json" \
  -d '{
    "menu": {
      "client_id": "test_client",
      "franchise_id": "test_store",
      "locale": "es-CO",
      "version": 1,
      "items": []
    }
  }'
```

## Notes and caveats

- The app currently uses Google Speech Recognition (`recognize_google`) for transcription.
- The model is loaded at startup if a valid checkpoint exists.
- If no model is available, `/predict` returns a `503` error.
- The app uses a blue/green model approach via `nlu_model_1` and `nlu_model_2` to swap after menu updates.
- This is a local prototype and is not production hardened for multi-user deployment, authentication, or persistent storage beyond the local file-based menu cache.

## License

This project does not currently declare a license in the repository root. If you plan to distribute it publicly, add a license file such as MIT or Apache 2.0.

## Summary

`prediction-api` is a lightweight voice-order inference service for restaurant ordering. It combines:

- Flask web endpoints,
- Google speech transcription,
- a Hugging Face NER pipeline,
- fuzzy matching against a menu catalog,
- dynamic menu updates and model slot swapping.

It is designed to convert spoken orders into a structured JSON payload suitable for downstream ordering systems.
