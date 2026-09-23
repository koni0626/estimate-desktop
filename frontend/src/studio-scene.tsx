export function StudioScene({
  onDesk,
  onPost,
  unread,
}: {
  onDesk: () => void;
  onPost: () => void;
  unread: number | null;
}) {
  return (
    <div className="studio-scene">
      <svg
        viewBox="0 0 610 340"
        role="img"
        aria-label="陽の差す窓、デスク、観葉植物のある小さなアトリエ"
      >
        <defs>
          <linearGradient id="wall" x2="0" y2="1">
            <stop stopColor="#f7e7cc" />
            <stop offset="1" stopColor="#ebd6b4" />
          </linearGradient>
          <linearGradient id="floor" x2="1" y2="1">
            <stop stopColor="#eedbbb" />
            <stop offset="1" stopColor="#d4b28b" />
          </linearGradient>
          <linearGradient id="sky" x2="0" y2="1">
            <stop stopColor="#b9d8d0" />
            <stop offset="1" stopColor="#e5eed6" />
          </linearGradient>
          <filter id="soft">
            <feGaussianBlur stdDeviation="6" />
          </filter>
        </defs>
        <ellipse
          cx="324"
          cy="293"
          rx="236"
          ry="24"
          fill="#aa9778"
          opacity=".13"
          filter="url(#soft)"
        />
        <path
          d="M110 210 299 304 551 177 362 84Z"
          fill="url(#floor)"
          stroke="#ccad85"
          strokeWidth="2"
        />
        <path d="M110 210 299 304v10L110 220z" fill="#caa681" />
        <path d="M299 304 551 177v10L299 314z" fill="#bd9874" />
        <path
          d="M110 210V62L298 154v150z"
          fill="url(#wall)"
          stroke="#ddc6a5"
          strokeWidth="2"
        />
        <path
          d="M298 154 551 29v148L298 304z"
          fill="#f5ead5"
          stroke="#ddc6a5"
          strokeWidth="2"
        />
        <path
          d="M110 207 298 299 551 174"
          fill="none"
          stroke="#c9ac89"
          strokeWidth="7"
        />
        <g stroke="#d4b894" opacity=".6">
          <path d="m147 228 252-127M184 246l252-127M222 265l252-127M260 284l252-127" />
        </g>
        <path d="m354 142 96-48v88l-96 48z" fill="#f7e3a1" opacity=".5" />
        <path d="m384 211 90-46 53 27-92 47z" fill="#fff5c7" opacity=".6" />
        <path d="m335 121 102-51v76l-102 52z" fill="#b99b77" />
        <path d="m342 125 88-44v60l-88 45z" fill="url(#sky)" />
        <path d="m342 161 88-43v23l-88 45z" fill="#adbea1" opacity=".6" />
        <path d="m386 102v62m-44-9 88-44" stroke="#fcf2dc" strokeWidth="6" />
        <path d="m331 200 111-55 7 6-111 56z" fill="#c5a47d" />
        <path d="m338 207 111-56v7l-111 56z" fill="#b9936e" />
        <path d="m475 83 37-19v43l-37 19z" fill="#c8ab85" />
        <path d="m480 87 27-14v30l-27 14z" fill="#fff7e8" />
        <path
          d="m484 108 8-14 7 1 5-10"
          stroke="#819471"
          fill="none"
          strokeWidth="3"
        />
        <path d="m134 101 37 18v34l-37-18z" fill="#c2a080" />
        <path d="m139 108 27 13v23l-27-13z" fill="#f6f0de" />
        <path d="m145 119 14 7m-14 0 10 5" stroke="#aaae8c" strokeWidth="3" />
        <ellipse
          cx="300"
          cy="263"
          rx="83"
          ry="32"
          fill="#8c9a79"
          opacity=".44"
        />
        <ellipse
          cx="300"
          cy="263"
          rx="72"
          ry="26"
          fill="#aaba90"
          opacity=".6"
        />
        <path
          d="m213 204 124-64 124 61-124 64z"
          fill="#efd1a4"
          stroke="#ba9671"
          strokeWidth="2"
        />
        <path d="m213 204 124 61v9l-124-61z" fill="#c29b70" />
        <path d="m337 265 124-64v9l-124 64z" fill="#b08864" />
        <path
          d="M223 215v45l9 5v-45m214-9v40l-9 5v-41M334 274v33l9-5v-31"
          fill="#9c7d5e"
        />
        <path d="m268 202 60-29 44 22-60 30z" fill="#75877a" />
        <path d="m312 225 60-30v4l-60 30-44-22v-5z" fill="#597164" />
        <path
          d="m325 174-2-49 56 27 2 49z"
          fill="#526d61"
          stroke="#42594f"
          strokeWidth="3"
        />
        <path d="m329 170-1-37 45 21 1 37z" fill="#d6e6cc" />
        <g strokeWidth="2" strokeLinecap="round">
          <path
            d="m335 146 13 6m-13 1 29 14m-29-6 18 8m-18-1 24 12"
            stroke="#8fa888"
          />
          <path d="m355 156 9 5" stroke="#ca9e78" />
        </g>
        <path d="m341 182 26 13-17 8-27-13z" fill="#bdd0b6" opacity=".7" />
        <path d="m247 195 27-14 27 13-27 15z" fill="#fff4da" stroke="#bdac8d" />
        <path d="m254 194 18-9m-12 13 18-9" stroke="#c6c9ac" strokeWidth="2" />
        <g className="steam">
          <path
            d="M400 181q-5-8 1-15m7 19q-5-8 0-14"
            stroke="#faf6e9"
            strokeWidth="3"
            fill="none"
            strokeLinecap="round"
          />
        </g>
        <ellipse cx="404" cy="203" rx="14" ry="7" fill="#bea280" />
        <path
          d="M395 190v12q9 10 18 0v-12"
          fill="#e3a178"
          stroke="#af7959"
          strokeWidth="1.5"
        />
        <ellipse cx="404" cy="190" rx="9" ry="4" fill="#f7dec1" />
        <ellipse cx="404" cy="190" rx="6" ry="2.5" fill="#977352" />
        <path
          d="M414 193q11 0 4 9l-5 1"
          stroke="#c28660"
          strokeWidth="3"
          fill="none"
        />
        <ellipse
          cx="230"
          cy="257"
          rx="27"
          ry="11"
          fill="#b3997a"
          opacity=".4"
        />
        <path d="m217 235-4 29m26-20 7 25" stroke="#927454" strokeWidth="5" />
        <path
          d="M209 234q19-12 40 0v10q-18 13-40-1z"
          fill="#9ba685"
          stroke="#768266"
          strokeWidth="2"
        />
        <path
          d="M210 239v-37q18-10 37 5v29"
          fill="#a9b797"
          stroke="#768266"
          strokeWidth="3"
        />
        <g>
          <path d="m145 170 26 13-1 23q-10 8-22-6z" fill="#d19871" />
          <ellipse
            cx="158"
            cy="176"
            rx="17"
            ry="8"
            fill="#ddb38d"
            transform="rotate(26 158 176)"
          />
          <path
            d="M159 177v-44m0 32-15-18m15 9 15-19"
            stroke="#708b62"
            strokeWidth="4"
          />
          <ellipse
            cx="145"
            cy="145"
            rx="7"
            ry="13"
            fill="#9aaa7b"
            transform="rotate(-38 145 145)"
          />
          <ellipse
            cx="171"
            cy="138"
            rx="7"
            ry="14"
            fill="#7c956b"
            transform="rotate(30 171 138)"
          />
          <ellipse cx="159" cy="127" rx="8" ry="14" fill="#a5b183" />
        </g>
        <path d="m487 156 27-14 24 12-27 14z" fill="#e5c09a" />
        <path d="m487 156 24 12v33l-24-12z" fill="#c39b75" />
        <path d="m511 168 27-14v33l-27 14z" fill="#b08a66" />
        <path d="m491 164 15 7m-15 7 15 7" stroke="#936f50" strokeWidth="2" />
        <path d="m490 148 17-8 22 11-18 9z" fill="#f4e6cb" />
        <path d="m493 142 18-9 20 10-19 9z" fill="#b6c3a4" />
        <path d="m495 136 18-9 19 10-19 9z" fill="#dda185" />
        <ellipse
          cx="398"
          cy="267"
          rx="28"
          ry="11"
          fill="#b69e80"
          opacity=".35"
        />
        <path
          d="M374 263q-4-20 18-17 24-11 30 8 9 14-17 17-22 3-31-8"
          fill="#f7edda"
          stroke="#c8b294"
          strokeWidth="1.6"
        />
        <path
          d="m374 251 1-13 11 9m9-1 9-9 1 11"
          fill="#f7edda"
          stroke="#c8b294"
          strokeWidth="1.6"
        />
        <path
          d="m379 254 5 1m8 0 5-1"
          stroke="#8b7f69"
          strokeWidth="2"
          strokeLinecap="round"
        />
        <path
          d="M416 263q14-5 2-13"
          fill="none"
          stroke="#e7d8bc"
          strokeWidth="6"
        />
        <g fill="#d9ba7d" opacity=".7">
          <path d="m211 88 2 5 5 2-5 2-2 5-2-5-5-2 5-2z" />
          <path d="m482 31 2 4 4 2-4 2-2 4-2-4-4-2 4-2z" />
        </g>
      </svg>
      <button className="room-hotspot desk-hotspot" onClick={onDesk}>
        <span />
        デスクをひらく <b>↗</b>
      </button>
      <button className="room-hotspot post-hotspot" onClick={onPost}>
        <span className={unread ? "unread-dot" : ""} />
        次の一歩メモ <b>{unread ?? "…"}</b>
      </button>
      <span className="room-caption">自分のペースで、いい仕事を。</span>
    </div>
  );
}
