/**
 * Coach's whiteboard behind every page: a chalk pitch, a couple of set plays
 * that draw themselves, and paper grain. Pure SVG + CSS, no client JS.
 */
export function TacticsBackground() {
  return (
    <div className="tactics" aria-hidden="true">
      <div className="tactics-glow" />
      <svg
        className="tactics-pitch"
        viewBox="0 0 1050 680"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
      >
        <g className="chalk">
          <rect x="30" y="30" width="990" height="620" rx="4" />
          <line x1="525" y1="30" x2="525" y2="650" />
          <circle cx="525" cy="340" r="92" />
          <circle cx="525" cy="340" r="3" className="chalk-dot" />
          <rect x="30" y="178" width="165" height="324" />
          <rect x="30" y="263" width="55" height="154" />
          <path d="M195 268 A92 92 0 0 1 195 412" />
          <rect x="855" y="178" width="165" height="324" />
          <rect x="965" y="263" width="55" height="154" />
          <path d="M855 268 A92 92 0 0 0 855 412" />
        </g>

        {/* Play 1: a one-two down the right that ends in a cross */}
        <g className="play play-1">
          <path className="run" d="M640 520 C700 470 760 470 820 430" />
          <path className="pass" d="M600 430 L760 380" />
          <path className="run" d="M760 380 C820 330 880 300 930 330" />
          <text x="628" y="532" className="mark">X</text>
          <text x="590" y="440" className="mark">X</text>
          <circle cx="930" cy="330" r="9" className="mark-o" />
        </g>

        {/* Play 2: switch of play from the left back */}
        <g className="play play-2">
          <path className="pass" d="M150 560 C300 420 380 260 470 160" />
          <path className="run" d="M300 600 C360 540 420 520 480 470" />
          <text x="138" y="572" className="mark">X</text>
          <circle cx="470" cy="160" r="9" className="mark-o" />
        </g>
      </svg>
      <div className="grain" />
    </div>
  );
}
