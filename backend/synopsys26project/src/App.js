import Navbar from "./components/Navbar";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./components/Home";
import AddData from "./components/AddData";
import "./App.css";
import Results from "./components/Results";
import PatientData from "./components/PatientData";
import ProfileSection from "./components/ProfileSectoin";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/add-data" element={<AddData />} />
        <Route path="/patient-data" element={<PatientData />} />
        <Route path="/patient/:id" element={<ProfileSection />} />
        <Route path="/results" element={<Results />} />
      </Routes>
    </Router>
  );
}

export default App;
