"use client";
// AuthShowcasePanel.jsx
// Right-side panel for the Grak AI login page.
// Replaces the old video. Needs only React + Tailwind (no extra packages).

import { useEffect, useState } from "react";

const PREFIX = "Ask Grak AI to ";
const LINES = [
  "explain any topic step by step.",
  "search the web live.",
  "generate diagrams and images.",
  "debug your code.",
  "analyze your PDFs.",
  "build your portfolio.",
];

const TYPE_MS = 28; // typing speed
const ERASE_MS = 12; // backspace speed
const HOLD_MS = 1200; // pause after a line is complete
const GAP_MS = 250; // pause before the next line

function useTypewriter(lines) {
  const [text, setText] = useState("");

  useEffect(() => {
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setText(lines[0]);
      return;
    }

    let line = 0;
    let count = 0;
    let mode = "type"; // 'type' | 'erase'
    let timer;

    const tick = () => {
      const current = lines[line];
      if (mode === "type") {
        count += 1;
        setText(current.slice(0, count));
        if (count >= current.length) {
          mode = "erase";
          timer = setTimeout(tick, HOLD_MS);
        } else {
          timer = setTimeout(tick, TYPE_MS + Math.random() * 40);
        }
      } else {
        count -= 1;
        setText(current.slice(0, Math.max(count, 0)));
        if (count <= 0) {
          mode = "type";
          line = (line + 1) % lines.length;
          timer = setTimeout(tick, GAP_MS);
        } else {
          timer = setTimeout(tick, ERASE_MS);
        }
      }
    };

    timer = setTimeout(tick, 600);
    return () => clearTimeout(timer);
  }, [lines]);

  return text;
}

export default function AuthShowcasePanel({ onSubmit }) {
  const typed = useTypewriter(LINES);

  return (
    <div className="relative h-[440px] w-full overflow-hidden rounded-[28px] border border-white/5 bg-[#07040d] lg:h-[calc(100vh-150px)] lg:max-h-[760px]">
      {/* Animated black / purple / white gradient */}
      <div
        className="grak-glow absolute -inset-[20%] blur-[28px]"
        aria-hidden="true"
      />

      {/* Prompt bar */}
      <div className="absolute inset-0 flex items-center justify-center px-5">
        <div className="grak-bar flex w-full max-w-[500px] items-center justify-between gap-3 rounded-2xl py-3 pl-6 pr-2.5 text-[#0b0b0f]">
          <div className="min-h-[26px] truncate text-base font-semibold sm:text-[18px]">
            <span>{PREFIX}</span>
            <span>{typed}</span>
            <span className="grak-caret" aria-hidden="true" />
          </div>
          <button
            type="button"
            aria-label="Send"
            onClick={onSubmit}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#1c1c1f] transition hover:scale-105 hover:bg-violet-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-500"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#fff"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Component-scoped CSS (gradient, glass bar, caret, motion) */}
      <style>{`
        .grak-glow {
          background:
            radial-gradient(60% 45% at 50% 108%, #ffffff 0%, #e4d4ff 22%, rgba(168,85,247,0) 70%),
            radial-gradient(75% 55% at 50% 92%, #a855f7 0%, #7c3aed 38%, rgba(76,29,149,0) 75%),
            radial-gradient(45% 50% at 6% 60%, rgba(124,58,237,.85), transparent 70%),
            radial-gradient(45% 50% at 94% 60%, rgba(147,51,234,.85), transparent 70%),
            radial-gradient(40% 40% at 50% 15%, #000 0%, transparent 80%);
          animation: grak-drift 12s ease-in-out infinite alternate;
        }
        @keyframes grak-drift { to { transform: translate(0, -3%) scale(1.06); } }
        .grak-bar {
          background: rgba(255,255,255,.78);
          -webkit-backdrop-filter: blur(18px);
          backdrop-filter: blur(18px);
          box-shadow: 0 18px 50px -12px rgba(76,29,149,.55), inset 0 0 0 1px rgba(255,255,255,.6);
        }
        .grak-caret {
          display: inline-block; width: 2px; height: 20px; margin-left: 2px;
          vertical-align: middle; background: #7c3aed;
          animation: grak-blink 1s steps(1) infinite;
        }
        @keyframes grak-blink { 50% { opacity: 0; } }
        @media (prefers-reduced-motion: reduce) {
          .grak-glow, .grak-caret { animation: none; }
        }
      `}</style>
    </div>
  );
}
