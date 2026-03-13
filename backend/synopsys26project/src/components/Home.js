import "./Home.css";
import { useNavigate } from "react-router-dom";

export default function Home() {
    const navigate = useNavigate();

  return (
    <main className="home">
      <div className="home__container">
        <h1 className="home__title">Tumor Classification</h1>
        <div className="home__underline" />

        <div className="home__grid">
          {/* Left text + button */}
          <section className="home__left">
            <p className="home__blurb">
              Detect tumor
              <br />
              malignancy with
              <br />
              high accuracy
            </p>

            <button 
              className="pillButton" 
              type="button"
              onClick={() => navigate("/patient-data")}
              >
              patient data
            </button>
          </section>

          {/* Right card */}
          <section className="home__card" aria-label="New Patient">
            <h2 className="home__cardTitle">New Patient</h2>
            <p className="home__cardText">
              Enter the patient’s
              <br />
              FNA sample for
              <br />
              grading
            </p>

            <button
                className="pillButton pillButton--withArrow"
                type="button"
                onClick={() => navigate("/add-data")}
                >
                add data <span className="pillButton__arrow">→</span>
            </button>

          </section>
        </div>
      </div>
    </main>
  );
}
