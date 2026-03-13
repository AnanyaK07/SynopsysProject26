import "./PatientData.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "";

export default function PatientData() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/patients`)
      .then((res) => res.json())
      .then((data) => {
        setPatients(data.patients || []);
      })
      .catch(() => setPatients([]))
      .finally(() => setLoading(false));
  }, []);

  const handlePatientClick = (patientId) => {
    navigate(`/patient/${patientId}`);
  };

  return (
    <main className="pdata">
      <div className="pdata__container">
        <div className="pdata__headerRow">
          <button
            className="pdata__back"
            type="button"
            onClick={() => navigate(-1)}
          >
            ←
          </button>

          <div className="pdata__titleWrap">
            <h1 className="pdata__title">Patient Data</h1>
            <div className="pdata__underline" />
          </div>

          <div className="pdata__spacer" />
        </div>

        {loading ? (
          <p className="pdata__loading">Loading patients...</p>
        ) : patients.length === 0 ? (
          <p className="pdata__empty">
            No patients yet. Upload a CSV from the Add Data page.
          </p>
        ) : (
          <ul className="pdata__list" role="list">
            {patients.map((p) => {
              const isMalignant = p.label === "Malignant";
              const severityText = isMalignant
                ? p.severity || p.label
                : "Benign";

              return (
                <li key={p.id} className="pdata__item">
                  <button
                    type="button"
                    className="pdata__row"
                    onClick={() => handlePatientClick(p.id)}
                  >
                    <span className="pdata__id">Patient {p.id}</span>
                    <span
                      className={`pdata__badge pdata__badge--${
                        isMalignant ? "malignant" : "benign"
                      }`}
                    >
                      {severityText}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}

        <button
          className="pdata__upload"
          type="button"
          onClick={() => navigate("/add-data")}
          aria-label="Upload new data"
        >
          <span className="pdata__uploadIcon">↑</span>
        </button>
      </div>
    </main>
  );
}
