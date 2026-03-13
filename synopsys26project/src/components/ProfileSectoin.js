import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import "./ProfileSection.css";

const API_BASE = process.env.REACT_APP_API_BASE || "";

// Mock/Placeholder for the Ring component since it wasn't in the snippet
const Ring = ({ percent }) => (
  <div className="ring-placeholder" style={{ fontWeight: 'bold' }}>
    {percent}% Match
  </div>
);

function ProfileSection() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    fetch(`${API_BASE}/api/patients/${id}`)
      .then((res) => {
        if (!res.ok) throw new Error("Patient not found");
        return res.json();
      })
      .then(setPatient)
      .catch((err) => {
        console.error(err);
        setPatient(null);
      })
      .finally(() => setLoading(false));
  }, [id]);

  // Handle Loading State properly
  if (loading) return <div className="loading">Loading patient profile...</div>;

  // Handle "Not Found" or Error state
  if (!patient) return <div className="error">Patient record not found.</div>;

  // Derived data logic
  const pct = Math.round((patient.confidence || 0) * 100);
  const diagnosis = patient.diagnosis || patient.label || "Unknown";
  const severity = patient.severity || (diagnosis === "Malignant" ? "Standard Risk" : "Benign / No Severity Grade");
  
  // Define missing variables for the UI
  const meaning = diagnosis === "Malignant" 
    ? "High probability of cellular abnormality requiring immediate follow-up."
    : "Low probability of malignancy; routine monitoring suggested.";
    
  const nextSteps = patient.nextSteps || [
    "Consult with lead oncologist",
    "Schedule follow-up biopsy",
    "Review SHAP feature importance"
  ];

  return (
    <main className="profile">
      <div className="profile__container">
        <div className="profile__headerRow">
          <button
            className="profile__back"
            type="button"
            onClick={() => navigate("/patient-data")}
          >
            ←
          </button>
          <div className="profile__titleWrap">
            <h1 className="profile__title">Patient {patient.id}</h1>
            <div className="profile__underline" />
          </div>
          <div className="profile__spacer" />
        </div>

        <div className="profile__grid">
          <section className="profile__card">
            <h2 className="profile__cardTitle">Confidence:</h2>
            <div className="profile__confidenceValue">{pct}%</div>
            <div className="profile__confidenceHint">(model certainty estimate)</div>
          </section>

          <section className="profile__card profile__card--center">
            <h2 className="profile__cardTitle profile__cardTitle--center">Conclusion:</h2>
            <div className="profile__ringRow">
              <Ring percent={pct} />
            </div>
            <div className="profile__label">{diagnosis}</div>
            <div className="profile__severity">Subtype: {severity}</div>
            <p className="profile__meaning">{meaning}</p>
            <button
              className="profile__link"
              type="button"
              onClick={() => navigate("/patient-data")}
            >
              Back to Patient List
            </button>
          </section>

          <section className="profile__card">
            <h2 className="profile__cardTitle">Next Steps:</h2>
            <ul className="profile__list">
              {nextSteps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </section>
        </div>
    {/* Local Analysis: Waterfall + Decision Funnel */}
        <section className="profile__card profile__card--wide">
          <div className="profile__headerGroup">
            <h2 className="profile__cardTitle">Diagnostic Reasoning (Local AI Analysis)</h2>
            <p className="profile__subtitle">Understanding how the model reached this specific conclusion</p>
          </div>

          <div className="profile__visualizationsGrid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginTop: '20px' }}>
            
            {/* 1. Waterfall Plot */}
            <div className="profile__vizBox">
              <h3 style={{ fontSize: '1rem', marginBottom: '10px', textAlign: 'center' }}>Feature Impact (Waterfall)</h3>
              {patient.shap_graph ? (
                <img 
                  src={`data:image/png;base64,${patient.shap_graph}`} 
                  alt="SHAP Waterfall Plot" 
                  style={{ width: '100%', borderRadius: '8px', border: '1px solid #eee' }}
                />
              ) : <p className="profile__loading-text">Loading waterfall plot...</p>}
            </div>

            {/* 2. Decision Path (Funnel) */}
            <div className="profile__vizBox">
              <h3 style={{ fontSize: '1rem', marginBottom: '10px', textAlign: 'center' }}>Decision Path (Funnel)</h3>
              {patient.shap_decision ? (
                <img 
                  src={`data:image/png;base64,${patient.shap_decision}`} 
                  alt="SHAP Decision Plot" 
                  style={{ width: '100%', borderRadius: '8px', border: '1px solid #eee' }}
                />
              ) : <p className="profile__loading-text">Loading decision funnel...</p>}
            </div>
          </div>
          
          <div className="profile__caption" style={{ marginTop: '15px', borderTop: '1px solid #eee', paddingTop: '10px' }}>
            <p style={{ fontSize: '0.85rem', color: '#666', fontStyle: 'italic' }}>
              <strong>Interpretation:</strong> The Waterfall plot shows the individual contribution of each feature. 
              The Funnel plot shows the cumulative journey—where the lines move decisively indicates model certainty.
            </p>
          </div>
        </section>

        {/* Global Analysis (Only for Malignant cases) */}
        {patient.diagnosis === "Malignant" && patient.shap_summary && (
          <section className="profile__card profile__card--wide">
            <h2 className="profile__cardTitle">Global SHAP Analysis: Top Features Driving Malignancy</h2>
            <div className="profile__shapSummaryContainer" style={{ textAlign: 'center', marginTop: '20px' }}>
              <img 
                src={`data:image/png;base64,${patient.shap_summary}`} 
                alt="SHAP Summary Plot" 
                style={{ maxWidth: '100%', height: 'auto', borderRadius: '8px' }}
              />
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export default ProfileSection;