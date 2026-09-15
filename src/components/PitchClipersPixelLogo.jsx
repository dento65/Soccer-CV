import { useId } from "react";

export function PitchClipersPixelLogo({ animated = false, compact = false, className = "" }) {
  const svgId = useId().replaceAll(":", "");
  const titleId = `${svgId}-pitchclipers-logo-title`;
  const clipId = `${svgId}-pitchclipers-pitch-inner`;
  const rootClassName = ["pixel-logo", animated ? "is-animated" : "", compact ? "is-compact" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <svg
      className={rootClassName}
      viewBox={compact ? "20 50 660 320" : "0 0 720 520"}
      role="img"
      aria-labelledby={titleId}
    >
      <title id={titleId}>PitchClipers</title>
      <defs>
        <clipPath id={clipId}>
          <polygon points="106,213 151,126 482,126 612,224 592,332 113,332 73,288" />
        </clipPath>
      </defs>
      <rect width="720" height={compact ? "430" : "520"} fill="transparent" />
      <g className="logo-pixels">
        <polygon className="logo-ink" points="78,198 139,105 499,105 640,211 623,346 104,352 42,296" />
        <polygon className="logo-ink-2" points="110,326 590,326 577,351 106,352 51,300" />
        <polygon className="logo-green" points="106,213 151,126 482,126 612,224 592,332 113,332 73,288" />
        <g clipPath={`url(#${clipId})`}>
          <polygon fill="#45c928" points="80,332 132,332 217,126 165,126" />
          <polygon className="logo-green-2" points="135,332 190,332 274,126 220,126" />
          <polygon fill="#27a91e" points="190,332 248,332 333,126 277,126" />
          <polygon className="logo-green-2" points="249,332 306,332 391,126 335,126" />
          <polygon fill="#38c221" points="307,332 365,332 449,126 392,126" />
          <polygon className="logo-lime clipped-zone" points="370,332 592,332 561,247 474,174 425,211" />
          <g fill="#16991d" opacity="0.95">
            <rect x="411" y="254" width="8" height="8" />
            <rect x="438" y="245" width="7" height="7" />
            <rect x="467" y="261" width="8" height="8" />
            <rect x="493" y="251" width="6" height="6" />
            <rect x="525" y="277" width="8" height="8" />
            <rect x="552" y="300" width="7" height="7" />
            <rect x="424" y="297" width="7" height="7" />
            <rect x="450" y="315" width="8" height="8" />
            <rect x="489" y="318" width="7" height="7" />
            <rect x="531" y="334" width="8" height="8" />
            <rect x="570" y="348" width="7" height="7" />
          </g>
        </g>
        <polyline className="logo-line" points="106,213 151,126 482,126 612,224 592,332 113,332 73,288 106,213" />
        <line className="logo-line" x1="343" y1="126" x2="343" y2="332" />
        <circle className="logo-line" cx="343" cy="230" r="42" />
        <rect className="logo-white" x="336" y="223" width="14" height="14" />
        <polyline className="logo-line-thin" points="131,244 183,244 205,292 137,292 116,267" />
        <polyline className="logo-line-thin" points="118,221 160,221 174,253 133,253" />
        <rect className="logo-white" x="168" y="265" width="10" height="10" />
        <polyline className="logo-line-thin" points="514,239 566,245 587,292 533,292 502,265" />
        <polyline className="logo-line-thin" points="551,253 576,257 589,281 566,281" />
        <rect className="logo-white" x="531" y="267" width="10" height="10" />

        <g className="clipper" transform="translate(395 44) scale(0.82) rotate(9 92 160)">
          <polygon className="logo-ink clapper-top" points="42,54 298,14 314,59 62,102" />
          <rect className="logo-white" x="76" y="54" width="40" height="31" transform="rotate(-9 96 69)" />
          <rect className="logo-white" x="156" y="39" width="40" height="31" transform="rotate(-9 176 54)" />
          <rect className="logo-white" x="237" y="26" width="40" height="31" transform="rotate(-9 257 41)" />
          <polygon className="logo-ink-2 clipper-body" points="58,110 241,84 266,236 88,266" />
          <polygon fill="#f9fbf8" points="85,124 210,106 229,218 106,239" />
          <polygon className="logo-ink" points="134,147 185,173 143,210" />
          <rect className="logo-lime" x="229" y="126" width="20" height="67" />
          <rect className="logo-ink" x="76" y="252" width="154" height="22" />
          <g className="logo-white">
            <rect x="83" y="270" width="10" height="46" />
            <rect x="105" y="267" width="10" height="49" />
            <rect x="127" y="264" width="10" height="52" />
            <rect x="149" y="261" width="10" height="55" />
            <rect x="171" y="258" width="10" height="58" />
            <rect x="193" y="255" width="10" height="61" />
          </g>
          <rect className="logo-ink-2" x="43" y="94" width="214" height="22" />
          <circle className="logo-ink" cx="55" cy="82" r="29" />
          <circle fill="#dff2e3" cx="55" cy="82" r="12" />
          <rect className="logo-green-2" x="226" y="211" width="31" height="31" />
        </g>

        <g className="logo-lime logo-particles">
          <rect className="motion-particle p1" x="408" y="171" width="15" height="15" />
          <rect className="motion-particle p2" x="382" y="198" width="12" height="12" />
          <rect className="motion-particle p3" x="425" y="211" width="10" height="10" />
          <rect className="motion-particle p4" x="398" y="238" width="12" height="12" />
          <polygon className="motion-particle p5" points="340,168 358,168 343,201 365,201 331,248 343,214 321,214" />
          <polygon className="motion-particle p6" points="603,203 621,203 607,234 630,234 596,282 608,247 586,247" />
          <rect className="motion-particle p7" x="617" y="276" width="12" height="12" />
          <rect className="motion-particle p8" x="635" y="306" width="14" height="14" />
          <rect className="motion-particle p9" x="604" y="316" width="11" height="11" />
        </g>
      </g>

      {!compact && (
        <text x="52" y="488" className="logo-word">
          <tspan fill="#56d22d">Pitch</tspan>
          <tspan fill="#ffffff">Clipers</tspan>
        </text>
      )}
    </svg>
  );
}
