import "./Navbar.css";
import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <div className="navbar__brand">app name</div>

        <Link to="/" className="navbar__home" aria-label="Home">
          {/* inline SVG house icon */}
          <svg
            className="navbar__icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 11.5L12 4l9 7.5" />
            <path d="M5 10.5V20h14v-9.5" />
          </svg>
          <span className="navbar__homeText">home</span>
        </Link>
      </div>
    </header>
  );
}
