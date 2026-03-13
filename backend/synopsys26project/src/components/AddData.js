import "./AddData.css";
import { useNavigate } from "react-router-dom";
import { useState, useRef } from "react";

const API_BASE = process.env.REACT_APP_API_BASE || "";

export default function AddData() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/upload-csv`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data.missing?.length
          ? `Missing columns: ${data.missing.join(", ")}`
          : data.error || "Upload failed";
        setError(msg);
        setLoading(false);
        return;
      }

      navigate("/patient-data", { state: { imported: data.patients?.length } });
    } catch (err) {
      setError(err.message || "Network error");
    } finally {
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <main className="pd">
      <div className="pd__container">
        <div className="pd__headerRow">
          <button className="pd__back" type="button" onClick={() => navigate(-1)}>
            ←
          </button>

          <div className="pd__titleWrap">
            <h1 className="pd__title">Patient Bio-Metrics</h1>
            <div className="pd__underline" />
          </div>

          <div className="pd__spacer" />
        </div>

        <section className="pd__card">
          <form
            className="pd__form"
            onSubmit={(e) => {
              e.preventDefault();
              fileInputRef.current?.click();
            }}
          >
            <label className="pd__field">
              <span className="pd__label">Upload Wisconsin Breast Cancer CSV</span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="pd__input"
                style={{ paddingTop: 12, paddingBottom: 12 }}
                onChange={handleFileChange}
                disabled={loading}
              />
            </label>

            {error && (
              <p style={{ color: "#c00", margin: 0, fontSize: 16 }}>{error}</p>
            )}

            {loading && (
              <p style={{ margin: 0, opacity: 0.8 }}>Processing CSV...</p>
            )}

            <div className="pd__actions">
              <button
                className="pd__submit"
                type="submit"
                disabled={loading}
              >
                {loading ? "Processing..." : "Choose CSV to Upload"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
