"use client";

/**
 * ComposerActions: the right side of the Grak AI composer.
 * Empty input  -> [mic] [voice (waveform) button]
 * Typing       -> [mic] [purple send button]  (voice button morphs into send)
 *
 * Props
 *  hasText     true when the input has non-whitespace text
 *  onSend      called when the send button is clicked
 *  onMic       called when the mic (dictation) button is clicked
 *  onVoice     called when the voice button is clicked
 *  listening   true while dictation is recording (mic turns purple)
 *  busy        true while a response is streaming (send is disabled)
 */
export default function ComposerActions({
  hasText = false,
  onSend,
  onMic,
  onVoice,
  listening = false,
  busy = false,
}) {
  return (
    <div className={`gca ${hasText ? "gca-typing" : ""}`}>
      <style>{CSS}</style>

      <button
        type="button"
        className={`gca-ib ${listening ? "gca-listening" : ""}`}
        aria-label="Dictate"
        title="Dictate"
        onClick={onMic}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <rect x="9" y="3" width="6" height="12" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
        </svg>
      </button>

      <button
        type="button"
        className="gca-act"
        aria-label={hasText ? "Send message" : "Start voice mode"}
        title={hasText ? "Send" : "Voice mode"}
        disabled={hasText && busy}
        onClick={hasText ? onSend : onVoice}
      >
        {/* waveform icon (shown when the input is empty) */}
        <span className="gca-ico gca-wave" aria-hidden="true">
          <svg
            className="gca-bars"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <rect x="2" y="9" width="2.6" height="6" rx="1.3" />
            <rect x="6.8" y="5" width="2.6" height="14" rx="1.3" />
            <rect x="11.6" y="2.5" width="2.6" height="19" rx="1.3" />
            <rect x="16.4" y="6.5" width="2.6" height="11" rx="1.3" />
            <rect x="21" y="10" width="2.2" height="4" rx="1.1" />
          </svg>
        </span>
        {/* up-arrow icon (shown while typing) */}
        <span className="gca-ico gca-send" aria-hidden="true">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 19V5M5 12l7-7 7 7" />
          </svg>
        </span>
      </button>
    </div>
  );
}

const CSS = `
.gca{display:flex;align-items:center;gap:4px}
.gca svg{display:block}
.gca-ib{background:none;border:0;padding:0;width:36px;height:36px;border-radius:50%;display:grid;place-items:center;
  color:#d4d4dc;cursor:pointer;transition:color .15s ease,background-color .15s ease}
.gca-ib:hover{color:#fff;background:rgba(255,255,255,.06)}
.gca-listening{color:#fff;background:#7c3aed}
.gca-act{position:relative;width:36px;height:36px;border-radius:50%;border:0;padding:0;cursor:pointer;
  background:rgba(255,255,255,.09);color:#fff;transition:background-color .2s ease,transform .25s ease}
.gca-act:disabled{opacity:.5;cursor:not-allowed}
.gca-ib:focus-visible,.gca-act:focus-visible{outline:2px solid #e4d4ff;outline-offset:2px}
.gca-ico{position:absolute;inset:0;display:grid;place-items:center;transition:opacity .2s ease,transform .25s ease}
.gca-send{opacity:0;transform:scale(.4) rotate(-60deg)}
.gca-typing .gca-act{background:#7c3aed}
.gca-typing .gca-act:hover:not(:disabled){background:#8b5cf6}
.gca-typing .gca-send{opacity:1;transform:none}
.gca-typing .gca-wave{opacity:0;transform:scale(.4) rotate(60deg)}
.gca-bars rect{transform-box:fill-box;transform-origin:center}
@media (hover:hover){
  .gca:not(.gca-typing) .gca-act:hover{transform:translateY(-2px)}
  .gca:not(.gca-typing) .gca-act:hover .gca-bars rect{animation:gcaLvl .9s ease-in-out infinite}
  .gca-bars rect:nth-child(2){animation-delay:.08s!important}
  .gca-bars rect:nth-child(3){animation-delay:.16s!important}
  .gca-bars rect:nth-child(4){animation-delay:.24s!important}
  .gca-bars rect:nth-child(5){animation-delay:.32s!important}
}
@keyframes gcaLvl{0%,100%{transform:scaleY(.4)}50%{transform:scaleY(1.15)}}
@media (prefers-reduced-motion:reduce){
  .gca-act,.gca-ico{transition:none}
  .gca-act:hover .gca-bars rect{animation:none!important}
}
`;
