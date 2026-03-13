import "./Results.css";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000";

export default function Results() {
  const navigate = useNavigate();
  const { id } = useParams(); // Gets ID from URL (e.g., /patient/123)
  const { state } = useLocation();

  // 1. Initialize state with passed data, otherwise null
  const [patient, setPatient] = useState(state || null);
  const [loading, setLoading] = useState(!state && !!id);

  // 2. Fetch data if we only have an ID (e.g., coming from the Patient List)
  useEffect(() => {
    if (!patient && id) {
      setLoading(true);
      fetch(`${API_BASE}/api/patients/${id}`)
        .then((res) => res.json())
        .then((data) => {
          setPatient({
            label: data.diagnosis,
            confidence: data.confidence,
            meaning: data.severity,
            shap_graph: data.shap_graph,
            nextSteps: data.diagnosis === "Malignant" 
              ? ["Urgent biopsy", "Consult oncologist", "Lymph node check"] 
              : ["Routine monitoring", "Follow-up in 12 months"]
          });
        })
        .catch((err) => console.error("Error fetching patient:", err))
        .finally(() => setLoading(false));
    }
  }, [id, patient]);

  // Handle case where there is no data at all
  if (loading) return <div className="results__loading">Generating AI Analysis...</div>;
  
  const result = patient || {
    label: "No Data",
    confidence: 0,
    meaning: "Please select a patient or upload a CSV.",
    nextSteps: [],
    shap_graph: null
  };

  const pct = Math.round((result.confidence || 0) * 100);

  return (
    <main className="results">
      <div className="results__container">
        <h1 className="results__title">Diagnostic Results</h1>
        <div className="results__underline" />

        <div className="results__grid">
          {/* Confidence card */}
          <section className="results__card">
            <h2 className="results__cardTitle">Confidence:</h2>
            <div className="results__confidenceValue">{pct}%</div>
            <div className="results__confidenceHint">(model certainty estimate)</div>
          </section>

          {/* Conclusion card */}
          <section className="results__card results__card--center">
            <h2 className="results__cardTitle results__cardTitle--center">Conclusion:</h2>
            <div className="results__ringRow">
              <Ring percent={pct} />
            </div>
            <div className="results__label">{result.label}</div>
            <p className="results__meaning">{result.meaning}</p>
          </section>

          {/* Next steps card */}
          <section className="results__card">
            <h2 className="results__cardTitle">Next Steps:</h2>
            <ul className="results__list">
              {(result.nextSteps || []).map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </section>

          {/* NEW: Diagnostic Reasoning Card (Full Width) */}
          
          {/* Replace the "FNA Features" section with this Diagnostic Reasoning section */}
<section className="results__card results__card--fullwidth">
  <h2 className="results__cardTitle">Diagnostic Reasoning:</h2>
  <p className="results__subtitle">AI Explainability (SHAP Waterfall Plot)</p>
  
  {result.shap_graph ? (
    <div className="results__shapContainer">
      <img 
        src={`data:image/png;base64,${result.shap_graph}`} 
        alt="SHAP Explanation Graph" 
        className="results__shapImage"
      />
      <div className="results__caption">
        <p><b>How to read this:</b> Features in <b>red</b> pushed the model towards a Malignant prediction, 
        while <b>blue</b> features pushed it towards Benign.</p>
      </div>
    </div>
  ) : (
    <div className="results__loading-placeholder">
      <p>Generating explainability data... if this persists, check the backend console for SHAP errors.</p>
    </div>
  )}
</section>
        </div>

        <div className="results__actions">
           <button className="pillButton" onClick={() => navigate("/patient-data")}>
              Back to Patient List
           </button>
        </div>
      </div>
    </main>
  );
}

// ... Ring component remains same as your original code ...
function Ring({ percent = 0 }) {
  const r = 88;
  const c = 2 * Math.PI * r;
  const clamped = Math.max(0, Math.min(100, percent));
  const offset = c * (1 - clamped / 100);

  return (
    <div className="ring">
      <svg className="ring__svg" viewBox="0 0 220 220">
        <circle className="ring__track" cx="110" cy="110" r={r} />
        <circle
          className="ring__progress"
          cx="110"
          cy="110"
          r={r}
          strokeDasharray={c}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring__centerText">{clamped}%</div>
    </div>
  );
}