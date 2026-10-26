from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path

import joblib
import pandas as pd
from flask import Flask, jsonify, request

deployment_root = Path(__file__).resolve().parents[1]
if (deployment_root / "common" / "contracts.py").is_file():
    sys.path.insert(0, str(deployment_root))

from common.contracts import MODEL_FEATURES, validate_model_record

MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", Path(__file__).with_name("superkart_model.joblib"))
)
if not MODEL_PATH.is_file():
    raise FileNotFoundError(
        f"Model artifact not found at {MODEL_PATH}. Run the submission notebook first."
    )

model = joblib.load(MODEL_PATH)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


@app.get("/")
def index():
    return jsonify(
        {
            "status": "ok",
            "model": "SuperKart sales regression pipeline",
            "endpoints": ["POST /v1/predict", "POST /v1/predictbatch"],
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": True})


@app.post("/v1/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    try:
        # Reject unsupported categories before sending data to the estimator.
        row = validate_model_record(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    try:
        value = float(model.predict(pd.DataFrame([row], columns=MODEL_FEATURES))[0])
    except (TypeError, ValueError, RuntimeError):
        app.logger.exception("Model prediction failed for a valid single-row request.")
        return jsonify({"error": "Prediction failed; inspect the server log."}), 500
    return jsonify(
        {"Predicted_Product_Store_Sales_Total": round(value, 2), "warnings": []}
    )


@app.post("/v1/predictbatch")
def predict_batch():
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"error": "Attach a CSV file using the 'file' field."}), 400

    try:
        frame = pd.read_csv(io.BytesIO(uploaded.read()))
    except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        return jsonify({"error": f"Could not read uploaded CSV: {exc}."}), 400

    missing = [field for field in MODEL_FEATURES if field not in frame.columns]
    extra = [field for field in frame.columns if field not in MODEL_FEATURES]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing columns: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected columns: {', '.join(map(str, extra))}")
        return jsonify({"error": "; ".join(details)}), 400
    if frame.empty:
        return jsonify({"error": "The uploaded CSV contains no data rows."}), 400

    valid_rows: list[tuple[int, dict[str, object]]] = []
    errors = []
    # Preserve source row numbers while allowing valid rows to predict in one call.
    for row_number, (_, series) in enumerate(frame.iterrows(), start=1):
        try:
            valid_rows.append(
                (row_number, validate_model_record(series.to_dict()))
            )
        except ValueError as exc:
            errors.append({"row": row_number, "message": str(exc)})

    predictions = []
    if valid_rows:
        try:
            features = pd.DataFrame(
                [row for _, row in valid_rows], columns=MODEL_FEATURES
            )
            values = model.predict(features)
        except (TypeError, ValueError, RuntimeError):
            app.logger.exception("Model prediction failed for a valid batch request.")
            return jsonify({"error": "Batch prediction failed; inspect the server log."}), 500
        predictions = [
            {
                "row": row_number,
                "Predicted_Product_Store_Sales_Total": round(float(value), 2),
            }
            for (row_number, _), value in zip(valid_rows, values, strict=True)
        ]

    return jsonify(
        {
            "rows_received": len(frame),
            "predicted_count": len(predictions),
            "error_count": len(errors),
            "predictions": predictions,
            "errors": errors,
            "warnings": [],
        }
    )


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Uploaded file exceeds the 20 MB limit."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "7860")))
