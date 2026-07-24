/** Schmale Full-Bleed-Leiste — ruhiges Signalmotiv, ohne Marken-Doppelung */
export function LagebildRibbon() {
  return (
    <div className="lagebild-ribbon" aria-hidden="true">
      <svg
        className="lagebild-ribbon-svg"
        viewBox="0 0 1440 72"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="ribbon-base" x1="0%" y1="50%" x2="100%" y2="50%">
            <stop offset="0%" stopColor="#0d4a3e" />
            <stop offset="55%" stopColor="#0f6e56" />
            <stop offset="100%" stopColor="#1e3832" />
          </linearGradient>
          <linearGradient id="ribbon-line" x1="0%" y1="50%" x2="100%" y2="50%">
            <stop offset="0%" stopColor="#e8e4da" stopOpacity="0" />
            <stop offset="35%" stopColor="#e8e4da" stopOpacity="0.4" />
            <stop offset="70%" stopColor="#b8d4c8" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#e8e4da" stopOpacity="0" />
          </linearGradient>
        </defs>

        <rect width="1440" height="72" fill="url(#ribbon-base)" />

        <path
          className="ribbon-wave ribbon-wave-a"
          d="M0 40 C240 22, 420 54, 720 36 S1200 18, 1440 42"
          fill="none"
          stroke="url(#ribbon-line)"
          strokeWidth="1.4"
        />
        <path
          className="ribbon-wave ribbon-wave-b"
          d="M0 48 C300 60, 560 30, 880 46 S1200 58, 1440 38"
          fill="none"
          stroke="#e8e4da"
          strokeOpacity="0.16"
          strokeWidth="1"
        />

        <g className="ribbon-nodes" fill="#f3f1eb" fillOpacity="0.85">
          <circle cx="360" cy="38" r="2.2" />
          <circle cx="720" cy="36" r="2.6" />
          <circle cx="1080" cy="40" r="2.2" />
        </g>
      </svg>
    </div>
  );
}
