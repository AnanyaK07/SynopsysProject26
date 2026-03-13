"""
Flask API for breast cancer classification.
Endpoints: POST /api/upload-csv, GET /api/patients, GET /api/patients/<id>
"""
import os
import json
import uuid
import numpy as np  # Required for array reshaping
from io import StringIO
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

from model_service import (
    get_or_create_model,
    preprocess_df,
    predict_from_df,
    normalize_csv_columns,
    REQUIRED_FEATURES,
    get_patient_diagnosis,
    generate_shap_waterfall_base64,
    generate_shap_decision_base64
)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Keep load_patients and save_patients inside app.py as they currently are
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "patients.json")

def load_patients():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_patients(patients):
    with open(DATA_FILE, "w") as f:
        json.dump(patients, f, indent=2)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/required-columns", methods=["GET"])
def required_columns():
    """List the 24 feature columns the model expects. Alternate names (e.g. 'mean radius') are accepted."""
    return jsonify({"required": REQUIRED_FEATURES})


@app.route("/api/upload-csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        content = file.read().decode("utf-8")
        df_raw = pd.read_csv(StringIO(content))
    except Exception as e:
        return jsonify({"error": f"Invalid CSV: {str(e)}"}), 400

    # Normalize columns (accepts Wisconsin, UCI, sklearn, or any CSV with equivalent names)
    try:
        df_mapped, id_values, missing = normalize_csv_columns(df_raw)
    except Exception as e:
        return jsonify({"error": f"Column mapping failed: {str(e)}"}), 400

    if missing:
        return jsonify({
            "error": f"Missing required columns: {', '.join(missing)}. The model needs all 24 features. See /api/required-columns for the full list.",
            "missing": missing,
        }), 400

    ids = id_values if id_values else [str(uuid.uuid4())[:8] for _ in range(len(df_raw))]

    try:
        df_clean = preprocess_df(df_mapped)
    except Exception as e:
        return jsonify({"error": f"Preprocessing failed: {str(e)}"}), 400

    patients = load_patients()
    new_patients = []

    # Use the two-stage pipeline per row
    for i, row in df_clean.iterrows():
        features_array = row.to_numpy().reshape(1, -1)
        diag = get_patient_diagnosis(features_array)

        diagnosis = diag["diagnosis"]
        severity = diag["severity"]
        prob = float(diag["probability"])
        pred = int(diag["raw_pred"])
        label = diagnosis  # keep malignant/benign label for compatibility
        

        patient_id = ids[i] if i < len(ids) else str(uuid.uuid4())[:8]

        # Build feature dict from row (for display)
        # Build feature dict from original raw row (for display)
        raw_row = df_raw.iloc[i]
        record = raw_row.to_dict()
        record = {k: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else str(v))
                  for k, v in record.items() if pd.notna(v) and k not in ["Unnamed: 32"]}

        patient = {
            "id": patient_id,
            "label": label,
            "diagnosis": diagnosis,
            "severity": severity,
            "confidence": prob if pred == 1 else (1.0 - prob),
            "raw_pred": pred,
            "features": record,
        }
        patients.append(patient)
        new_patients.append(patient)

    save_patients(patients)
    return jsonify({"patients": new_patients, "total": len(patients)})


@app.route("/api/patients", methods=["GET"])
def list_patients():
    patients = load_patients()
    summary = []
    
    for p in patients:
        # We use .get() to avoid errors if a key is missing
        # The 'confidence' in p is already calculated during upload
        summary.append({
            "id": p.get("id"),
            "label": p.get("label", p.get("diagnosis", "")),
            "confidence": p.get("confidence", 0), 
            "severity": p.get("severity"),
        })
        
    return jsonify({"patients": summary})


@app.route("/api/patients/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    """
    Retrieves a single patient record and generates live SHAP 
    visualizations (Waterfall and Decision plots) for the profile view.
    """
    # 1. Load the current list of patients from the JSON database
    patients = load_patients()
    
    # 2. Locate the specific patient by their ID
    patient = next((p for p in patients if str(p["id"]) == str(patient_id)), None)
    
    if patient:
        try:
            # 3. Reconstruct the feature array required for SHAP explainers
            # We pull the 24 canonical features from the patient's stored record
            features_dict = patient.get("features", {})
            vals = [float(features_dict.get(c, 0)) for c in REQUIRED_FEATURES]
            
            # Reshape for a single prediction: (1, 24)
            feat_array = np.array(vals).reshape(1, -1)
            
            # 4. Generate the Waterfall Plot (Horizontal Bars)
            # This shows the magnitude of individual feature impacts
            patient["shap_graph"] = generate_shap_waterfall_base64(
                feat_array, 
                REQUIRED_FEATURES
            )
            
            # 5. Generate the Decision Plot (The "Funnel")
            # This shows the cumulative journey of the model's decision
            patient["shap_decision"] = generate_shap_decision_base64(
                feat_array, 
                REQUIRED_FEATURES
            )

            # 6. Optional: Generate Global Summary Plot for Malignant cases
            # This is used for the "Global Model Context" section in your React code
            if patient.get("diagnosis") == "Malignant":
                from model_service import generate_shap_summary_base64
                patient["shap_summary"] = generate_shap_summary_base64(
                    feat_array, 
                    REQUIRED_FEATURES
                )
            else:
                patient["shap_summary"] = None

        except Exception as e:
            # Log the specific error (e.g., the matrix shape error) for debugging
            app.logger.error(f"Diagnostic graph generation failed for patient {patient_id}: {e}")
            
            # Ensure the keys exist so the React frontend doesn't encounter 'undefined'
            patient.setdefault("shap_graph", None)
            patient.setdefault("shap_decision", None)
            patient.setdefault("shap_summary", None)
            
        return jsonify(patient)
    
    # Return a 404 if the patient ID does not exist in patients.json
    return jsonify({"error": "Patient not found"}), 404

if __name__ == "__main__":
    # Ensure model is loaded on startup
    get_or_create_model()
    app.run(host="0.0.0.0", port=5000, debug=True)
