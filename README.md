# Prediction API

A voice-driven order prediction service that turns spoken restaurant orders into structured JSON output using speech recognition and a transformer-based NER pipeline.

The project combines three core capabilities:

- audio capture and transcription,
- menu-aware entity extraction,
- post-processing into a structured order payload.

The result is an API that can interpret spoken orders, match them against the active restaurant menu, and return a normalized order representation ready for downstream systems.

## What this project solves

The service addresses a common operational problem in food-service environments: converting natural spoken requests into machine-readable orders without requiring manual entry.

Instead of a cashier or kiosk needing to interpret every spoken order, this application handles:

- speech-to-text conversion,
- entity detection for items, quantities, and modifiers,
- fuzzy matching against a catalog of menu items,
- dynamic menu refreshes without redeploying the API.

## Why this matters

This project sits at the intersection of machine learning, backend engineering, and practical restaurant automation. It was designed to support a real ordering workflow where menu configuration can change and where model accuracy matters in noisy, conversational speech.

It demonstrates the ability to build a service that is not only model-driven, but also operationally aware:

- it validates client and franchise data,
- it swaps model versions safely,
- it manages the active menu in memory and on disk,
- it keeps the service usable even when the model is not immediately available.

## Tech stack

- Python
- Flask
- SpeechRecognition
- Hugging Face Transformers
- Fuzzy matching with RapidFuzz / fuzzywuzzy
- JSON-based menu management
- Local filesystem for model and menu artifacts

## System architecture

The application is structured as a small modular backend service.

### API layer

`app.py` is the entry point for the Flask service. It exposes two relevant endpoints:

- `GET /predict`
  - accepts a filename for an audio sample,
  - validates the file,
  - runs speech-to-text,
  - runs model inference,
  - returns a JSON order prediction.

- `POST /menu/update`
  - validates the incoming menu payload,
  - updates the active menu cache,
  - writes the menu document to disk,
  - reloads the active model slot.

### Menu management

The `menu/` package keeps menu state consistent and available to the prediction pipeline.

- `menu/cache.py` stores the active menu in memory.
- `menu/manager.py` validates and writes the menu, then exposes it to the rest of the app.
- `menu/menu_loader.py` loads menu JSON from disk into the runtime cache.

This allows the API to work with a current menu without hardcoding it into the application logic.

### Prediction pipeline

The `prediction/` package handles the reasoning layer:

- `prediction/text_cleaner.py` normalizes transcript input before inference.
- `prediction/predictor.py` orchestrates the flow from spoken text to a structured order.

### Model loading and post-processing

The `model/` package is responsible for the ML runtime:

- `model/loader.py` finds the latest checkpoint in a model slot and loads the Hugging Face token-classification pipeline.
- `model/postprocessing.py` converts named entities into structured order items, quantity, and modifiers using alias matching and fuzzy resolution.

This is where the raw model output is transformed into a business-friendly result such as:

```json
{
  "items": [
    {
      "cantidad": 2,
      "producto": "Hamburguesa",
      "modificadores": ["con queso"]
    }
  ]
}
```

## Core workflow

```text
Audio file
  -> HTTP request to /predict
  -> validate file and payload
  -> SpeechRecognition (Google STT)
  -> normalize transcript
  -> Hugging Face NER model
  -> match entities to menu aliases
  -> structured order JSON returned to client
```

## File structure

```text
prediction-api/
├── app.py
├── config.py
├── requirements.txt
├── menu_items.json
├── audio_samples/
├── models/
│   └── test_client_test_store/
│       ├── nlu_model_1/
│       └── nlu_model_2/
├── menu/
│   ├── cache.py
│   ├── manager.py
│   ├── menu_loader.py
│   └── __init__.py
├── model/
│   ├── loader.py
│   ├── postprocessing.py
│   └── __init__.py
├── prediction/
│   ├── predictor.py
│   ├── text_cleaner.py
│   └── __init__.py
├── bin/
│   └── record-order
└── README.md
```

## Request examples

### Predict an order from an audio file

```http
GET /predict
Content-Type: application/json
```

Request body:

```json
{
  "filename": "order_01.wav"
}
```

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

### Update the menu dynamically

```http
POST /menu/update
Content-Type: application/json
```

Request body:

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

## Setup and run

### Prerequisites

- Python 3.10+
- pip
- access to internet for installing dependencies and fetching Hugging Face model files
- a local `audio_samples/` directory
- a trained NER checkpoint under the expected model directory structure

### 1. Clone the repository

```bash
git clone https://github.com/dfbello/prediction-api.git
cd prediction-api
```

### 2. Create a virtual environment

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

### 4. Prepare required folders

```bash
mkdir -p audio_samples
mkdir -p models/test_client_test_store/nlu_model_1
mkdir -p models/test_client_test_store/nlu_model_2
```

Place a trained model checkpoint into one of the model directories using the expected pattern:

```text
models/test_client_test_store/nlu_model_1/checkpoint-*/
```

The app automatically selects the newest `checkpoint-*` directory.

### 5. Provide a menu file

Create a root-level `menu_items.json` containing menu data for the active client and franchise.

Example:

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

### 6. Run the service

```bash
python app.py
```

The API will run locally on:

```text
http://127.0.0.1:5000
```

## Operational notes

- `config.py` defines the accepted `CLIENT_ID` and `FRANCHISE_ID` values.
- The app validates menu updates to prevent mismatched tenant data.
- The model uses a blue/green slot strategy with `nlu_model_1` and `nlu_model_2`.
- If no valid model is loaded, the prediction endpoint returns an error instead of attempting an invalid inference.
- The project is designed as a service prototype and can be extended with authentication, production deployment, and monitoring.

## Summary

This project demonstrates a practical full-stack AI workflow: turning spoken restaurant requests into structured machine-readable orders. It blends backend API development, speech recognition, ML model integration, and menu-aware post-processing into a single service that reflects real-world decision-making in voice-driven ordering systems.
