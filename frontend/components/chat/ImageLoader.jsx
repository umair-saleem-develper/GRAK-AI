"use client";
import { useEffect, useRef, useState } from "react";

/* Orb motion: two big lights moving in opposite directions */
const orbs = (t) => [
  [0.5 + 0.34 * Math.sin(0.9 * t), 0.5 + 0.3 * Math.sin(1.25 * t + 1), 0.16],
  [0.5 - 0.34 * Math.sin(0.9 * t + 0.5), 0.5 - 0.3 * Math.cos(1.05 * t), 0.16],
];

function DotCanvas() {
  const ref = useRef(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext("2d");
    if (!ctx) return;
    const reduce =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let W = 0,
      H = 0,
      raf = 0;
    const t0 = performance.now();

    const size = () => {
      if (!cv) return;
      const d = Math.min(window.devicePixelRatio || 1, 2);
      W = cv.clientWidth;
      H = cv.clientHeight;
      cv.width = W * d;
      cv.height = H * d;
      ctx.setTransform(d, 0, 0, d, 0, 0);
    };
    const ro = new ResizeObserver(size);
    ro.observe(cv);
    size();

    const draw = (now) => {
      const t = reduce ? 2 : (now - t0) / 1000;
      const os = orbs(t);
      ctx.clearRect(0, 0, W, H);
      for (const b of os) {
        const g = ctx.createRadialGradient(
          b[0] * W,
          b[1] * H,
          0,
          b[0] * W,
          b[1] * H,
          W * b[2] * 2.1,
        );
        g.addColorStop(0, "rgba(168,85,247,.30)");
        g.addColorStop(0.5, "rgba(124,58,237,.10)");
        g.addColorStop(1, "rgba(124,58,237,0)");
        ctx.fillStyle = g;
        ctx.fillRect(0, 0, W, H);
      }
      const cols = 26,
        pad = W * 0.06;
      const gx = (W - pad * 2) / (cols - 1);
      const rows = Math.round((H - pad * 2) / gx) + 1;
      const gy = (H - pad * 2) / (rows - 1);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const x = c / (cols - 1),
            y = r / (rows - 1);
          let f = 0;
          for (const b of os) {
            const dx = x - b[0],
              dy = y - b[1];
            f += Math.exp(-(dx * dx + dy * dy) / (2 * b[2] * b[2]));
          }
          f = Math.min(1, f);
          const rad = 0.45 + f * gx * 0.2;
          const al = 0.045 + Math.min(1, f * 1.15) * 0.95;
          const m = Math.min(1, Math.max(0, (f - 0.62) * 2));
          ctx.fillStyle = `rgba(${Math.round(124 + 104 * m)},${Math.round(58 + 154 * m)},${Math.round(237 + 18 * m)},${al})`;
          ctx.beginPath();
          ctx.arc(pad + c * gx, pad + r * gy, rad, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      if (!reduce) raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, []);
  return (
    <canvas
      ref={ref}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    />
  );
}

/**
 * Props:
 *  src          image URL (undefined while generating/searching)
 *  alt          alt text for the <img>
 *  label        animation label: "Creating image" | "Searching the web"
 *  onFail       called when image fails or times out
 *  timeoutMs    give up after this long (default 30 000 ms)
 *  minMs        minimum time animation plays before image reveals (default 1 500 ms)
 *  defaultRatio initial aspect ratio before real dimensions are known (default 1)
 *  children     rendered only when image is shown (use for overlay buttons)
 */
export default function ImageLoader({
  src,
  alt = "",
  label = "Creating image",
  onFail,
  timeoutMs = 30000,
  minMs = 1500,
  defaultRatio = 1,
  children,
}) {
  const [ratio, setRatio] = useState(defaultRatio);
  const [ready, setReady] = useState(false); // image downloaded
  const [shown, setShown] = useState(false); // after minMs gate
  const [failed, setFailed] = useState(false);
  const minDoneRef = useRef(false);
  const readyRef = useRef(false);

  // Min-animation gate
  useEffect(() => {
    const id = setTimeout(() => {
      minDoneRef.current = true;
      if (readyRef.current) setShown(true);
    }, minMs);
    return () => clearTimeout(id);
  }, [minMs]);

  // Timeout failsafe
  useEffect(() => {
    if (ready || failed) return;
    const id = setTimeout(() => {
      setFailed(true);
      onFail?.();
    }, timeoutMs);
    return () => clearTimeout(id);
  }, [ready, failed, timeoutMs, onFail]);

  if (failed) return null;

  const MAX = 560;
  const w = ratio >= 1 ? MAX : Math.round(MAX * ratio);

  return (
    <div
      style={{
        position: "relative",
        width: `min(100%, ${w}px)`,
        aspectRatio: String(ratio),
        borderRadius: 18,
        overflow: "hidden",
        background: shown ? "transparent" : "#030207",
      }}
    >
      <style>{`
        @keyframes grakShine{from{background-position:100% 0}to{background-position:0 0}}
        @media (prefers-reduced-motion: reduce){.grak-shine{animation:none!important;-webkit-text-fill-color:#e4d4ff!important}}
      `}</style>

      {/* Actual image — hidden until shown */}
      {src && (
        <img
          src={src}
          alt={alt}
          onLoad={(e) => {
            const img = e.currentTarget;
            if (img.naturalWidth && img.naturalHeight) {
              setRatio(img.naturalWidth / img.naturalHeight);
            }
            readyRef.current = true;
            setReady(true);
            if (minDoneRef.current) setShown(true);
          }}
          onError={() => {
            setFailed(true);
            onFail?.();
          }}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "cover",
            opacity: shown ? 1 : 0,
            filter: shown ? "none" : "blur(12px)",
            transition: "opacity .9s ease, filter .9s ease",
          }}
        />
      )}

      {/* Loading animation — hidden once shown */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: shown ? 0 : 1,
          transition: "opacity .7s ease",
          pointerEvents: "none",
        }}
      >
        <DotCanvas />
        <div
          className="grak-shine"
          style={{
            position: "absolute",
            left: 20,
            top: 18,
            fontSize: 17,
            fontWeight: 500,
            background:
              "linear-gradient(100deg,#6b5a8f 0%,#6b5a8f 35%,#e4d4ff 50%,#6b5a8f 65%,#6b5a8f 100%)",
            backgroundSize: "300% 100%",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
            WebkitTextFillColor: "transparent",
            animation: "grakShine 2.2s ease-in-out infinite alternate",
          }}
        >
          {label}
        </div>
      </div>

      {/* Children (zoom button etc.) — only when image is visible */}
      {shown && children}
    </div>
  );
}
