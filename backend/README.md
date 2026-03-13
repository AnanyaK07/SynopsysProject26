# Backend API

Breast cancer classification backend using the Random Forest model from the Synopsys notebook.

## Setup

```bash
cd backend
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

API runs at `http://localhost:5000`.

## Endpoints

- `POST /api/upload-csv` — Upload Wisconsin breast cancer CSV; returns imported patients
- `GET /api/patients` — List all patients (id, label, confidence)
- `GET /api/patients/<id>` — Full patient details and prediction

## CSV Format

Any CSV with the 24 required feature columns will work. Column names are flexible:

- **Wisconsin/Kaggle:** `radius_mean`, `texture_mean`, `concave points_mean`, etc.
- **Sklearn/UCI style:** `mean radius`, `texture error`, `worst concave points`, etc.
- **Case-insensitive**, spaces/underscores treated equivalently

Get the full list: `GET /api/required-columns`
