"""
Model service for breast cancer classification.
Replicates preprocessing and model from the Synopsys Jupyter notebook.
"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn import metrics
import joblib
import shap 
import matplotlib
import matplotlib.pyplot as plt
import io
import base64

matplotlib.use('Agg')
_shap_explainer = None
# Columns to remove (highly correlated, per notebook)
VARS_TO_REMOVE = [
    "perimeter_mean", "area_mean",
    "perimeter_worst", "area_worst",
    "radius_worst", "radius_se",
]

# Canonical feature names the model expects (24 columns)
REQUIRED_FEATURES = [
    "radius_mean", "texture_mean", "smoothness_mean", "compactness_mean",
    "concavity_mean", "concave points_mean", "symmetry_mean", "fractal_dimension_mean",
    "texture_se", "perimeter_se", "area_se", "smoothness_se", "compactness_se",
    "concavity_se", "concave points_se", "symmetry_se", "fractal_dimension_se",
    "texture_worst", "smoothness_worst", "compactness_worst", "concavity_worst",
    "concave points_worst", "symmetry_worst", "fractal_dimension_worst",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _normalize_col(s):
    """Normalize column name for matching: lowercase, underscores for spaces/hyphens."""
    return str(s).strip().lower().replace(" ", "_").replace("-", "_")


def _build_column_aliases():
    """Map alternate column names -> canonical names. Any CSV with these columns will work."""
    aliases = {}
    # Wisconsin/Kaggle: radius_mean, concave points_mean, etc.
    for c in REQUIRED_FEATURES:
        aliases[_normalize_col(c)] = c
    # Sklearn / UCI style: "mean radius", "radius error", "worst radius"
    sklearn_style = {
        "mean radius": "radius_mean", "mean texture": "texture_mean",
        "mean smoothness": "smoothness_mean", "mean compactness": "compactness_mean",
        "mean concavity": "concavity_mean", "mean concave points": "concave points_mean",
        "mean symmetry": "symmetry_mean", "mean fractal dimension": "fractal_dimension_mean",
        "texture error": "texture_se", "perimeter error": "perimeter_se", "area error": "area_se",
        "smoothness error": "smoothness_se", "compactness error": "compactness_se",
        "concavity error": "concavity_se", "concave points error": "concave points_se",
        "symmetry error": "symmetry_se", "fractal dimension error": "fractal_dimension_se",
        "worst texture": "texture_worst", "worst smoothness": "smoothness_worst",
        "worst compactness": "compactness_worst", "worst concavity": "concavity_worst",
        "worst concave points": "concave points_worst", "worst symmetry": "symmetry_worst",
        "worst fractal dimension": "fractal_dimension_worst",
    }
    for k, v in sklearn_style.items():
        aliases[_normalize_col(k)] = v
    # "radius mean" (space) -> radius_mean
    for c in REQUIRED_FEATURES:
        spaced = c.replace("_", " ")
        aliases[_normalize_col(spaced)] = c
    return aliases


COLUMN_ALIASES = _build_column_aliases()

def get_shap_explainer(model):
    global _shap_explainer
    if _shap_explainer is None:
        # Initializing the explainer for Random Forest
        _shap_explainer = shap.TreeExplainer(model)
    return _shap_explainer

def generate_shap_waterfall_base64(patient_features, feature_names):
    rf_model, _ = get_or_create_model() 
    explainer = get_shap_explainer(rf_model)
    
    X = pd.DataFrame(patient_features, columns=feature_names)
    shap_values = explainer(X)

    plt.figure(figsize=(10, 6))
    
    try:
        if hasattr(shap_values, "values"):
            # Slicing for: [first patient, all features, malignant class]
            shap.plots.waterfall(shap_values[0, :, 1], show=False)
        else:
            exp = shap.Explanation(
                values=shap_values[1][0], 
                base_values=explainer.expected_value[1], 
                data=X.iloc[0], 
                feature_names=feature_names
            )
            shap.plots.waterfall(exp, show=False)
    except Exception as e:
        print(f"Waterfall failed: {e}")
        shap.plots.bar(shap_values[0, :, 1], show=False)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generate_shap_decision_base64(patient_features, feature_names):
    rf_model, _ = get_or_create_model() 
    explainer = get_shap_explainer(rf_model)
    
    X = pd.DataFrame(patient_features, columns=feature_names)
    
    # Get raw SHAP values
    shap_values_raw = explainer.shap_values(X)
    
    # Select Malignant class (index 1) and its base value
    if isinstance(shap_values_raw, list):
        target_values = shap_values_raw[1]
        base_value = explainer.expected_value[1]
    else:
        target_values = shap_values_raw[:, :, 1]
        base_value = explainer.expected_value[1]

    plt.figure(figsize=(10, 8))
    
    # Generate the Funnel/Decision Plot
    shap.plots.decision(
        base_value, 
        target_values, 
        features=X, 
        show=False,
        feature_order='importance'
    )

    import io
    import base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def normalize_csv_columns(df):
    """
    Rename CSV columns to canonical feature names. Accepts Wisconsin, UCI, sklearn,
    or any CSV with equivalent column names (case-insensitive, spaces/underscores flexible).
    Returns (df_with_canonical_cols, id_col_values_or_none, missing_cols).
    """
    df = df.copy()
    id_values = None
    id_col = None

    # Detect ID column (optional): id, ID, patient_id, index, etc.
    for col in df.columns:
        norm = _normalize_col(col)
        if norm in ("id", "patient_id", "patientid", "index", "sample_id"):
            id_values = df[col].astype(str).tolist()
            id_col = col
            break

    if id_col:
        df = df.drop(columns=[id_col])

    rename_map = {}
    for col in df.columns:
        norm = _normalize_col(col)
        if norm in COLUMN_ALIASES:
            canonical = COLUMN_ALIASES[norm]
            if canonical in REQUIRED_FEATURES:
                rename_map[col] = canonical

    df = df.rename(columns=rename_map)

    # Keep only required feature columns; drop rest (diagnosis, Unnamed: 32, etc.)
    to_keep = [c for c in df.columns if c in REQUIRED_FEATURES]
    df = df[to_keep]

    missing = [c for c in REQUIRED_FEATURES if c not in df.columns]
    return df, id_values, missing


# Sklearn breast cancer uses different column names; map to Kaggle format
SKLEARN_TO_KAGGLE = {
    "mean radius": "radius_mean",
    "mean texture": "texture_mean",
    "mean perimeter": "perimeter_mean",
    "mean area": "area_mean",
    "mean smoothness": "smoothness_mean",
    "mean compactness": "compactness_mean",
    "mean concavity": "concavity_mean",
    "mean concave points": "concave points_mean",
    "mean symmetry": "symmetry_mean",
    "mean fractal dimension": "fractal_dimension_mean",
    "radius error": "radius_se",
    "texture error": "texture_se",
    "perimeter error": "perimeter_se",
    "area error": "area_se",
    "smoothness error": "smoothness_se",
    "compactness error": "compactness_se",
    "concavity error": "concavity_se",
    "concave points error": "concave points_se",
    "symmetry error": "symmetry_se",
    "fractal dimension error": "fractal_dimension_se",
    "worst radius": "radius_worst",
    "worst texture": "texture_worst",
    "worst perimeter": "perimeter_worst",
    "worst area": "area_worst",
    "worst smoothness": "smoothness_worst",
    "worst compactness": "compactness_worst",
    "worst concavity": "concavity_worst",
    "worst concave points": "concave points_worst",
    "worst symmetry": "symmetry_worst",
    "worst fractal dimension": "fractal_dimension_worst",
}


def treat_outliers(df, col):
    """Flooring and capping per notebook."""
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    df = df.copy()
    df[col] = np.clip(df[col], lower, upper)
    return df


def treat_outliers_all(df, col_list):
    for c in col_list:
        df = treat_outliers(df, c)
    return df


def preprocess_df(df):
    """
    Preprocess DataFrame for prediction. Expects df with canonical feature columns
    (from normalize_csv_columns). Applies outlier treatment per notebook.
    """
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df = treat_outliers_all(df, numeric_cols)
    return df


def train_model():
    """Train Random Forest model using sklearn breast cancer data.

    Kept for reference; the live API now prefers the two-stage pipeline
    models loaded from .pkl files.
    """
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    # Sklearn: 0=malignant, 1=benign. Map to notebook: 1=malignant, 0=benign
    y = 1 - data.target

    # Rename columns to Kaggle format
    X = X.rename(columns=SKLEARN_TO_KAGGLE)

    # Apply same feature removal
    for col in VARS_TO_REMOVE:
        if col in X.columns:
            X = X.drop(columns=[col])

    # Treat outliers
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    X = treat_outliers_all(X, numeric_cols)

    # Grid search (simplified - notebook's was commented out)
    rf = RandomForestClassifier(class_weight={0: 0.35, 1: 0.65}, random_state=1)
    params = {
        "max_depth": [5, 7, 9],
        "n_estimators": [50, 100],
        "min_samples_split": [2, 5],
    }
    grid = GridSearchCV(rf, params, scoring=metrics.make_scorer(metrics.recall_score), cv=3, n_jobs=-1)
    grid.fit(X, y)
    return grid.best_estimator_, list(X.columns)


def get_or_create_model():
    """Load cached model or train and cache."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(base_dir, "model.pkl")
    feature_path = os.path.join(base_dir, "feature_names.pkl")

    if os.path.exists(model_path) and os.path.exists(feature_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(feature_path, "rb") as f:
            feature_names = pickle.load(f)
        return model, feature_names

    model, feature_names = train_model()
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    with open(feature_path, "wb") as f:
        pickle.dump(feature_names, f)
    return model, feature_names


def predict_from_df(df, model=None, feature_names=None):
    """
    Run predictions on preprocessed DataFrame.
    Returns list of dicts: {id, diagnosis_label, probability, raw_pred}
    """
    if model is None or feature_names is None:
        model, feature_names = get_or_create_model()

    # Ensure we have the feature columns
    X = df[[c for c in feature_names if c in df.columns]].copy()
    missing = [c for c in feature_names if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1]  # P(malignant)

    return preds, probs


# ---------------------------------------------------------------------------
# Two-stage pipeline: RF gatekeeper + K-Means severity grader
# ---------------------------------------------------------------------------

_RF_MODEL_PATH = os.path.join(BASE_DIR, "cancer_detector_rf.pkl")
_SCALER_PATH = os.path.join(BASE_DIR, "unsupervised_scaler.pkl")
_KMEANS_PATH = os.path.join(BASE_DIR, "severity_grader_kmeans.pkl")

_rf_model = None
_scaler = None
_kmeans_model = None


def _load_two_stage_models():
    """
    Lazy-load the Random Forest gatekeeper, unsupervised scaler, and K-Means
    severity grader from the provided .pkl files.
    """
    global _rf_model, _scaler, _kmeans_model
    if _rf_model is not None and _scaler is not None and _kmeans_model is not None:
        return _rf_model, _scaler, _kmeans_model

    if not (os.path.exists(_RF_MODEL_PATH) and os.path.exists(_SCALER_PATH) and os.path.exists(_KMEANS_PATH)):
        raise FileNotFoundError(
            "Two-stage models not found. Expected 'cancer_detector_rf.pkl', "
            "'unsupervised_scaler.pkl', and 'severity_grader_kmeans.pkl' in the backend directory."
        )

    _rf_model = joblib.load(_RF_MODEL_PATH)
    _scaler = joblib.load(_SCALER_PATH)
    _kmeans_model = joblib.load(_KMEANS_PATH)
    return _rf_model, _scaler, _kmeans_model


def get_patient_diagnosis(patient_data_array):
    """
    Two-stage pipeline:
    1) Random Forest gatekeeper detects malignancy.
    2) If malignant, K-Means (on scaled features) assigns severity.

    patient_data_array: 2D numpy array of shape (1, n_features)
    Returns dict with:
      - diagnosis: "Malignant" or "Benign"
      - severity: "High Risk (Aggressive Subtype)", "Standard Risk",
                  or "Benign / No Severity Grade"
      - probability: model's certainty for the predicted diagnosis
      - raw_pred: 1 for malignant, 0 for benign
    """
    rf_model, scaler, kmeans_model = _load_two_stage_models()

    is_malignant = rf_model.predict(patient_data_array)[0]
    proba_malignant = float(rf_model.predict_proba(patient_data_array)[0][1])

    if is_malignant == 0:
        return {
            "diagnosis": "Malignant" if proba_malignant >= 0.5 else "Benign",
            "probability": proba_malignant,  # Always send the raw 0.0 to 1.0 value
            "raw_pred": 1 if proba_malignant >= 0.5 else 0,
            "severity": "High Risk" if proba_malignant > 0.7 else "Medium Risk" if proba_malignant >= 0.5 else "Low Risk"
        }

    scaled_data = scaler.transform(patient_data_array)
    cluster_id = int(kmeans_model.predict(scaled_data)[0])
    severity = "High Risk (Aggressive Subtype)" if cluster_id == 1 else "Standard Risk"

    return {
        "diagnosis": "Malignant",
        "severity": severity,
        "probability": proba_malignant,
        "raw_pred": 1,
    }
