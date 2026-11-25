"use client";
import React, { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/cjs/styles/prism";
import {
  Maximize2,
  X,
  ExternalLink,
  Copy,
  Check,
  Terminal,
  RefreshCw,
  Sparkles,
  Download,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Volume2,
  Pencil,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import "katex/dist/katex.min.css";
import ImageLoader from "@/components/chat/ImageLoader";

/**
 * Parses **bold** and `code` inside strings and strips bracketed labels
 */
export function renderFormattedInline(text) {
  if (!text) return null;
  const cleaned = text
    .replace(/\*\*\[([^\]]+)\]:\*\*/g, "**$1:**")
    .replace(/\[([^\]]+)\]:/g, "**$1:**");

  const parts = cleaned.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      const inner = part.slice(2, -2).replace(/^\[\vert{}\]$/g, "");
      return (
        <strong key={idx} className="font-bold text-white">
          {inner}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      const inner = part.slice(1, -1);
      return (
        <code
          key={idx}
          className="not-italic font-mono font-semibold text-[13.5px] text-[#E9D5FF] bg-[#1E1B30] border border-[#362C59] px-2 py-0.5 rounded-md mx-0.5"
        >
          {inner}
        </code>
      );
    }
    return <span key={idx}>{part}</span>;
  });
}

/**
 * Streaming-safe parser for :::visual-hero, :::visual-flow, :::visual-component, and :::generated-image blocks
 */
export function parseVisualContent(content) {
  if (!content) return [{ type: "markdown", content: "" }];
  const blocks = [];
  const blockRegex =
    /:::(visual-hero|visual-flow|visual-component|generated-image)\s*([\s\S]*?)(?::::|$)/g;
  let lastIndex = 0;
  let match;

  while ((match = blockRegex.exec(content)) !== null) {
    const textBefore = content.substring(lastIndex, match.index).trim();
    if (textBefore) blocks.push({ type: "markdown", content: textBefore });

    const blockType = match[1];
    const body = match[2];

    if (blockType === "visual-hero") {
      const imgMatch = body.match(/^image:\s*(.+)$/m);
      const titleMatch = body.match(/^title:\s*(.+)$/m);
      const srcMatch = body.match(/^source:\s*(.+)$/m);
      const srcUrlMatch = body.match(/^source_url:\s*(.+)$/m);
      blocks.push({
        type: "hero",
        image: imgMatch ? imgMatch[1].trim() : "",
        title: titleMatch ? titleMatch[1].trim() : "Visual Diagram",
        source: srcMatch ? srcMatch[1].trim() : "Web",
        source_url: srcUrlMatch ? srcUrlMatch[1].trim() : "",
      });
    } else if (blockType === "visual-flow") {
      // inputs: Name|url,Name|url
      // process: Title|url
      // outputs: Name|url
      const inpsMatch = body.match(/^inputs:\s*(.+)$/m);
      const procMatch = body.match(/^process:\s*(.+)$/m);
      const outsMatch = body.match(/^outputs:\s*(.+)$/m);

      const parseItems = (str) => {
        if (!str) return [];
        return str
          .split(",")
          .map((item) => {
            const [name, url] = item.split("|");
            return { name: (name || "").trim(), url: (url || "").trim() };
          })
          .filter((item) => item.name && item.url);
      };

      const procParts = procMatch ? procMatch[1].trim().split("|") : [];
      blocks.push({
        type: "flow",
        inputs: inpsMatch ? parseItems(inpsMatch[1]) : [],
        process: {
          title: procParts[0] || "Process",
          url: procParts[1] || "",
        },
        outputs: outsMatch ? parseItems(outsMatch[1]) : [],
      });
    } else if (blockType === "visual-component") {
      const imgMatch = body.match(/^image:\s*(.+)$/m);
      const titleMatch = body.match(/^title:\s*(.+)$/m);
      const bulletLines = body
        .split("\n")
        .map((l) => l.trim())
        .filter(
          (l) => l.startsWith("- ") || l.startsWith("* ") || l.startsWith("• "),
        )
        .map((l) => l.replace(/^[-*•]\s+/, "").trim());

      blocks.push({
        type: "component",
        image: imgMatch ? imgMatch[1].trim() : "",
        title: titleMatch ? titleMatch[1].trim() : "",
        bullets: bulletLines,
      });
    } else if (blockType === "generated-image") {
      const imgMatch = body.match(/^image:\s*(.+)$/m);
      const promptMatch = body.match(/^prompt:\s*(.+)$/m);
      blocks.push({
        type: "generated-image",
        image: imgMatch ? imgMatch[1].trim() : "",
        prompt: promptMatch ? promptMatch[1].trim() : "AI Generated Visual",
      });
    }
    lastIndex = match.index + match[0].length;
  }

  const trailing = content.substring(lastIndex).trim();
  if (trailing) blocks.push({ type: "markdown", content: trailing });
  return blocks;
}

/**
 * Hero Diagram Card: One large hero image card, labeled parts diagram, rounded-2xl, click-to-zoom.
 * Uses ImageLoader with "Searching the web" dot light animation.
 * If failed or timeout, onFail removes the card completely.
 */
export function VisualHeroCard({ block, onZoom }) {
  const [failed, setFailed] = useState(false);

  const imgSrc = block.image ? block.image.trim() : undefined;

  if (failed) return null;

  return (
    <div className="my-5">
      <ImageLoader
        src={imgSrc}
        alt={block.title || "Visual Diagram"}
        label="Searching the web"
        onFail={() => setFailed(true)}
      >
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (imgSrc && onZoom) onZoom(imgSrc, block.title);
          }}
          className="absolute bottom-4 right-4 px-2.5 py-1.5 rounded-lg bg-black/75 backdrop-blur-sm text-white opacity-0 hover:opacity-100 transition flex items-center gap-1.5 text-xs font-medium cursor-pointer z-10"
          title="Zoom image"
        >
          <Maximize2 className="w-3.5 h-3.5" />
          <span>Zoom</span>
        </button>
      </ImageLoader>
    </div>
  );
}

/**
 * Process Flow Component:
 * Small icon images for inputs joined by "+" signs, caption below (e.g. "Sunlight + Water + Carbon dioxide"),
 * down arrow (or horizontal arrow on desktop), one process diagram, output caption ("Food + Oxygen").
 * Responsive: wraps vertically on screens < 640px.
 */
export function ProcessFlowCard({ block, onZoom }) {
  const { inputs = [], process = {}, outputs = [] } = block;

  return (
    <div className="my-5 p-4 sm:p-5 rounded-2xl bg-[#12101B] border border-white/10 shadow-lg">
      <div className="flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Inputs Column */}
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2 flex-wrap justify-center">
            {inputs.map((inp, idx) => (
              <React.Fragment key={idx}>
                <div
                  onClick={() => inp.url && onZoom && onZoom(inp.url, inp.name)}
                  className="flex flex-col items-center group cursor-pointer"
                >
                  <ImageLoader
                    src={inp.url || undefined}
                    alt={inp.name}
                    label=""
                    defaultRatio={1}
                    onFail={() => {}}
                  />
                  <span className="text-[11px] text-gray-300 mt-1 font-medium text-center max-w-[70px] truncate">
                    {inp.name}
                  </span>
                </div>
                {idx < inputs.length - 1 && (
                  <span className="text-purple-400 font-bold text-lg mb-4">
                    +
                  </span>
                )}
              </React.Fragment>
            ))}
          </div>
          <span className="text-xs text-gray-400 font-medium mt-2">
            {inputs.map((i) => i.name).join(" + ")}
          </span>
        </div>

        {/* Down Arrow / Transition Indicator */}
        <div className="flex flex-col items-center justify-center my-1 md:my-0 text-purple-400 font-extrabold text-xl">
          <span className="hidden md:inline">➔</span>
          <span className="md:hidden">↓</span>
        </div>

        {/* Process Diagram Card */}
        {process.url && (
          <div
            onClick={() => onZoom && onZoom(process.url, process.title)}
            className="flex flex-col items-center cursor-pointer group max-w-[200px]"
          >
            <ImageLoader
              src={process.url}
              alt={process.title}
              label=""
              defaultRatio={16 / 10}
              onFail={() => {}}
            />
            <span className="text-xs text-white font-semibold mt-1 text-center truncate max-w-full">
              {process.title}
            </span>
          </div>
        )}

        {/* Transition Indicator */}
        <div className="flex flex-col items-center justify-center my-1 md:my-0 text-purple-400 font-extrabold text-xl">
          <span className="hidden md:inline">➔</span>
          <span className="md:hidden">↓</span>
        </div>

        {/* Outputs Column */}
        <div className="flex flex-col items-center">
          <div className="flex items-center gap-2 flex-wrap justify-center">
            {outputs.map((out, idx) => (
              <React.Fragment key={idx}>
                <div
                  onClick={() => out.url && onZoom && onZoom(out.url, out.name)}
                  className="flex flex-col items-center group cursor-pointer"
                >
                  <ImageLoader
                    src={out.url || undefined}
                    alt={out.name}
                    label=""
                    defaultRatio={1}
                    onFail={() => {}}
                  />
                  <span className="text-[11px] text-gray-300 mt-1 font-medium text-center max-w-[70px] truncate">
                    {out.name}
                  </span>
                </div>
                {idx < outputs.length - 1 && (
                  <span className="text-purple-400 font-bold text-lg mb-4">
                    +
                  </span>
                )}
              </React.Fragment>
            ))}
          </div>
          <span className="text-xs text-emerald-400 font-medium mt-2">
            {outputs.map((o) => o.name).join(" + ")}
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * Message Action Row:
 * Copy, Like, Dislike, Share, Read aloud, Regenerate, and tiny muted model pill.
 */
export function MessageActions({ content, provider, onRegenerate }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(null); // 'like' | 'dislike' | null
  const [speaking, setSpeaking] = useState(false);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({ title: "Grak AI Response", text: content });
    } else {
      handleCopy();
    }
  };

  const handleReadAloud = () => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const cleanText = content
      .replace(/:::[\s\S]*?:::/g, "")
      .replace(/[#*`_]/g, "");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="mt-2 flex items-center justify-start text-[#D4D4DC]">
      <div className="flex items-center gap-1">
        <button
          onClick={handleCopy}
          title="Copy response"
          aria-label="Copy response"
          className="w-9 h-9 rounded-full flex items-center justify-center text-[#D4D4DC] hover:text-white hover:bg-white/10 transition-colors"
        >
          {copied ? (
            <Check size={20} strokeWidth={2} className="text-emerald-400" />
          ) : (
            <Copy size={20} strokeWidth={2} />
          )}
        </button>

        <button
          onClick={() => setLiked(liked === "like" ? null : "like")}
          title="Good response"
          aria-label="Good response"
          className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
            liked === "like"
              ? "text-purple-400 bg-purple-500/10"
              : "text-[#D4D4DC] hover:text-white hover:bg-white/10"
          }`}
        >
          <ThumbsUp size={20} strokeWidth={2} />
        </button>

        <button
          onClick={() => setLiked(liked === "dislike" ? null : "dislike")}
          title="Bad response"
          aria-label="Bad response"
          className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
            liked === "dislike"
              ? "text-rose-400 bg-rose-500/10"
              : "text-[#D4D4DC] hover:text-white hover:bg-white/10"
          }`}
        >
          <ThumbsDown size={20} strokeWidth={2} />
        </button>

        <button
          onClick={handleShare}
          title="Share response"
          aria-label="Share response"
          className="w-9 h-9 rounded-full flex items-center justify-center text-[#D4D4DC] hover:text-white hover:bg-white/10 transition-colors"
        >
          <Share2 size={20} strokeWidth={2} />
        </button>

        {typeof window !== "undefined" && "speechSynthesis" in window && (
          <button
            onClick={handleReadAloud}
            title={speaking ? "Stop reading" : "Read aloud"}
            aria-label={speaking ? "Stop reading" : "Read aloud"}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-colors ${
              speaking
                ? "text-purple-400 bg-purple-500/10"
                : "text-[#D4D4DC] hover:text-white hover:bg-white/10"
            }`}
          >
            <Volume2
              size={20}
              strokeWidth={2}
              className={speaking ? "animate-pulse" : ""}
            />
          </button>
        )}

        {onRegenerate && (
          <button
            onClick={onRegenerate}
            title="Regenerate response"
            aria-label="Regenerate response"
            className="w-9 h-9 rounded-full flex items-center justify-center text-[#D4D4DC] hover:text-white hover:bg-white/10 transition-colors"
          >
            <RefreshCw size={20} strokeWidth={2} />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * AI Generated Image Card (FLUX.1 High-Fidelity Synthesis)
 */
export function GeneratedImageCard({ image, prompt, onZoom, onEdit }) {
  const [currentSrc, setCurrentSrc] = useState(image || undefined);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    setCurrentSrc(image || undefined);
    setHasError(false);
  }, [image]);

  const handleRetry = () => {
    setHasError(false);
    const cleanBase = (currentSrc || image || "").split(/[?&]seed=/)[0];
    const newSeed = Math.floor(Math.random() * 1000000);
    const separator = cleanBase.includes("?") ? "&" : "?";
    const retryUrl = `${cleanBase}${separator}seed=${newSeed}`;
    setCurrentSrc(retryUrl);
  };

  const handleDownload = (e) => {
    e.stopPropagation();
    if (!imgSrc) return;
    const link = document.createElement("a");
    link.href = imgSrc;
    link.download = `grak-image-${Date.now()}.png`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (hasError) return null; // never leave an empty box

  const imgSrc =
    currentSrc && currentSrc.trim() ? currentSrc.trim() : undefined;

  return (
    <div className="my-5 group/img">
      <ImageLoader
        src={imgSrc}
        alt={prompt || "AI Generated"}
        label="Creating image"
        onFail={() => setHasError(true)}
      >
        <div className="absolute bottom-3 right-3 flex items-center gap-1.5 opacity-100 sm:opacity-0 sm:group-hover/img:opacity-100 transition-opacity z-10">
          {onEdit && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                if (imgSrc) onEdit(imgSrc, prompt);
              }}
              className="px-2.5 py-1.5 rounded-lg bg-purple-600/90 hover:bg-purple-500 backdrop-blur-sm text-white transition flex items-center gap-1.5 text-xs font-medium cursor-pointer shadow-md"
              title="Edit this image"
            >
              <Pencil className="w-3.5 h-3.5" />
              <span>Edit</span>
            </button>
          )}
          <button
            type="button"
            onClick={handleDownload}
            className="p-1.5 rounded-lg bg-black/75 hover:bg-black/90 backdrop-blur-sm text-white transition flex items-center justify-center cursor-pointer"
            title="Download image"
            aria-label="Download image"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleRetry();
            }}
            className="p-1.5 rounded-lg bg-black/75 hover:bg-black/90 backdrop-blur-sm text-white transition flex items-center justify-center cursor-pointer"
            title="Retry / reload image"
            aria-label="Retry image"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (imgSrc && onZoom) {
                onZoom(
                  imgSrc,
                  prompt,
                  "",
                  "",
                  handleRetry,
                  onEdit ? () => onEdit(imgSrc, prompt) : undefined,
                );
              }
            }}
            className="px-2.5 py-1.5 rounded-lg bg-black/75 hover:bg-black/90 backdrop-blur-sm text-white transition flex items-center gap-1.5 text-xs font-medium cursor-pointer"
            title="Zoom image"
          >
            <Maximize2 className="w-3.5 h-3.5" />
            <span>Zoom</span>
          </button>
        </div>
      </ImageLoader>
    </div>
  );
}

/**
 * Custom Markdown Components with ChatGPT-style hierarchy
 */
export const grakMarkdownComponents = {
  h1: ({ children }) => (
    <h1 className="text-[22px] sm:text-[24px] font-extrabold text-white tracking-tight leading-snug mt-5 mb-3">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-[19px] sm:text-[21px] font-extrabold text-white tracking-tight leading-snug mt-5 mb-2.5">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-[17px] sm:text-[19px] font-bold text-white tracking-tight leading-snug mt-5 mb-2.5 flex items-center gap-2">
      {children}
    </h3>
  ),
  p: ({ children }) => (
    <p className="text-[15px] sm:text-[15.5px] font-normal text-[#E4E4E7] leading-[1.72] mb-3.5">
      {children}
    </p>
  ),
  ul: ({ children }) => (
    <ul className="list-disc pl-6 my-3 space-y-2 marker:text-[#A855F7]">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal pl-6 my-3 space-y-2 marker:text-[#A855F7] marker:font-bold">
      {children}
    </ol>
  ),
  li: ({ children }) => (
    <li className="text-[15px] sm:text-[15.5px] font-normal text-[#E4E4E7] leading-[1.68]">
      {children}
    </li>
  ),
  strong: ({ children }) => (
    <strong className="font-bold text-white">{children}</strong>
  ),
  blockquote: ({ children }) => (
    <blockquote className="not-italic border-l-4 border-[#A855F7] bg-[#18122B] px-5 py-4 my-5 rounded-r-xl shadow-lg text-[15px] sm:text-[15.5px] font-semibold text-white leading-relaxed">
      <div className="not-italic flex flex-wrap items-center gap-2 [&>p]:mb-0 [&>p]:not-italic [&>p]:font-semibold [&>p]:text-white">
        {children}
      </div>
    </blockquote>
  ),
  code: ({ inline, className, children, ...props }) => {
    const content = String(children).replace(/\n$/, "");
    if (inline || !className) {
      return (
        <code
          className="not-italic font-mono font-bold text-[14px] sm:text-[14.5px] text-[#F3E8FF] bg-[#261C47] border border-[#A855F7]/40 px-3 py-1 rounded-md tracking-[0.02em] mx-1 inline-block"
          {...props}
        >
          {content}
        </code>
      );
    }
    const match = /language-(\w+)/.exec(className || "");
    return (
      <div className="relative rounded-xl overflow-hidden my-6 border border-[#27273A] shadow-2xl bg-[#0D0D14] group">
        <div className="flex items-center justify-between px-4 py-2.5 bg-[#161622] border-b border-[#27273A]">
          <span className="text-[13px] font-mono text-[#A1A1AA] flex items-center gap-1.5">
            <Terminal size={12} /> {match ? match[1] : "text"}
          </span>
        </div>
        <SyntaxHighlighter
          language={match ? match[1] : "text"}
          style={oneDark}
          customStyle={{
            margin: 0,
            padding: "14px 16px",
            fontSize: "13.5px",
            lineHeight: "1.6",
            background: "transparent",
          }}
          wrapLongLines={true}
        >
          {content}
        </SyntaxHighlighter>
      </div>
    );
  },
  table: ({ children }) => (
    <div className="overflow-x-auto my-5 rounded-xl border border-[#2D2D44] bg-[#0F0F17] shadow-md">
      <table className="w-full border-collapse text-left">{children}</table>
    </div>
  ),
  thead: ({ children }) => (
    <thead className="bg-[#181826] border-b border-[#2D2D44]">{children}</thead>
  ),
  th: ({ children }) => (
    <th className="px-4 py-3 text-[14px] font-bold text-white tracking-wide">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="px-4 py-3 text-[14.5px] font-normal text-[#E4E4E7] border-t border-[#1F1F30] leading-relaxed">
      {children}
    </td>
  ),
  img: ({ src, alt }) => (
    <div className="my-4 rounded-xl overflow-hidden max-w-2xl">
      <ImageLoader src={src} alt={alt || "Image"} label="Searching the web" />
    </div>
  ),
};
/**
 * Zoom Modal — image only, dark backdrop, no white frame.
 * Floating Save / Regenerate / Close buttons. Escape key to close.
 */
function ZoomModal({ activeZoom, setActiveZoom }) {
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") setActiveZoom(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [setActiveZoom]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
      onClick={() => setActiveZoom(null)}
    >
      {/* Floating top-right action bar */}
      <div
        className="absolute top-4 right-4 z-10 flex items-center gap-2"
        onClick={(e) => e.stopPropagation()}
      >
        {activeZoom.onEdit && (
          <button
            onClick={() => {
              activeZoom.onEdit();
              setActiveZoom(null);
            }}
            className="h-9 px-3 rounded-full bg-purple-600/90 hover:bg-purple-500 text-white flex items-center gap-1.5 text-xs font-medium transition"
            title="Edit image"
            aria-label="Edit image"
          >
            <Pencil size={14} />
            <span>Edit</span>
          </button>
        )}

        {activeZoom.onRegenerate && (
          <button
            onClick={() => {
              activeZoom.onRegenerate();
              setActiveZoom(null);
            }}
            className="w-9 h-9 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-purple-500/60 transition"
            title="Regenerate"
            aria-label="Regenerate image"
          >
            <RefreshCw size={16} />
          </button>
        )}

        <button
          onClick={() =>
            activeZoom.image && window.open(activeZoom.image, "_blank")
          }
          className="w-9 h-9 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-black/80 transition"
          title="Save image"
          aria-label="Save image"
        >
          <Download size={16} />
        </button>

        <button
          onClick={() => setActiveZoom(null)}
          className="w-9 h-9 rounded-full bg-black/60 text-white flex items-center justify-center hover:bg-black/80 transition"
          aria-label="Close"
        >
          <X size={18} />
        </button>
      </div>

      {/* Image — NO white frame */}
      <motion.img
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        src={activeZoom.image}
        alt={activeZoom.title || "Preview"}
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: "90vw",
          maxHeight: "90vh",
          borderRadius: 18,
          objectFit: "contain",
          display: "block",
        }}
      />

      {/* Source link — floating bottom-left */}
      {activeZoom.source_url && (
        <a
          href={activeZoom.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="absolute bottom-4 left-4 z-10 text-xs text-purple-300 hover:text-purple-200 bg-black/60 px-3 py-1.5 rounded-full flex items-center gap-1"
          onClick={(e) => e.stopPropagation()}
        >
          Visit source <ExternalLink size={11} />
        </a>
      )}
    </motion.div>
  );
}

export default function ChatArea({
  messages,
  isGenerating,
  onRegenerate,
  onEditImage,
  zoomImage,
  setZoomImage,
}) {
  const [internalZoomImage, setInternalZoomImage] = useState(null);
  const activeZoom = zoomImage !== undefined ? zoomImage : internalZoomImage;
  const setActiveZoom = setZoomImage || setInternalZoomImage;

  return (
    <div className="w-full">
      <div className="flex flex-col space-y-6 pt-6">
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => {
            const role =
              msg.role === "ai" || msg.role === "assistant" ? "ai" : "user";
            const isError =
              msg.content?.includes("Error:") ||
              msg.content?.includes("HTTP 500");

            if (role === "user") {
              return (
                <motion.div
                  key={msg.id || idx}
                  initial={{ opacity: 0, y: 15, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="flex w-full justify-end mb-6"
                >
                  <div className="max-w-[85%] bg-[#1E1E2A] border border-[#2E2E42] text-[#F4F4F6] px-4 py-2.5 rounded-[18px] shadow-sm whitespace-pre-wrap text-[15.5px] leading-relaxed">
                    {msg.content}
                  </div>
                </motion.div>
              );
            }

            const parsedBlocks = parseVisualContent(msg.content);

            return (
              <motion.div
                key={msg.id || idx}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="flex w-full justify-start items-start gap-4 group mb-6"
              >
                <div className="flex-1 min-w-0 max-w-full">
                  {isError ? (
                    <div className="mt-2 bg-[#2a1315] border border-red-900/30 rounded-xl p-4">
                      <div className="text-red-200 font-medium mb-4">
                        {msg.content}
                      </div>
                      <button className="flex items-center gap-2 px-4 py-2 bg-[#3a1d1f] hover:bg-[#4a2527] border border-red-900/50 text-red-400 rounded-lg transition-colors text-sm font-medium shadow-sm">
                        <RefreshCw size={14} /> Retry Request
                      </button>
                    </div>
                  ) : (
                    <>
                      <div className="prose prose-invert max-w-none text-[#E4E4E7] text-[15.5px]">
                        {parsedBlocks.map((block, bIdx) => {
                          if (block.type === "generated-image") {
                            return (
                              <GeneratedImageCard
                                key={`gen-${bIdx}`}
                                image={block.image}
                                prompt={block.prompt}
                                onEdit={onEditImage}
                                onZoom={(img, title, src, url, onRegen, onEd) =>
                                  setActiveZoom({
                                    image: img,
                                    title: title || "AI Generated Visual",
                                    source: src,
                                    source_url: url,
                                    onRegenerate: onRegen,
                                    onEdit: onEd,
                                  })
                                }
                              />
                            );
                          }
                          if (block.type === "hero") {
                            return (
                              <VisualHeroCard
                                key={`hero-${bIdx}`}
                                block={block}
                                onZoom={(img, title) =>
                                  setActiveZoom({ image: img, title })
                                }
                              />
                            );
                          }
                          if (block.type === "flow") {
                            return (
                              <ProcessFlowCard
                                key={`flow-${bIdx}`}
                                block={block}
                                onZoom={(img, title) =>
                                  setActiveZoom({ image: img, title })
                                }
                              />
                            );
                          }
                          return (
                            <ReactMarkdown
                              key={`md-${bIdx}`}
                              remarkPlugins={[remarkGfm, remarkMath]}
                              rehypePlugins={[rehypeKatex]}
                              components={grakMarkdownComponents}
                            >
                              {block.content || " "}
                            </ReactMarkdown>
                          );
                        })}

                        {isGenerating && idx === messages.length - 1 && (
                          <span className="inline-flex gap-1 items-center ml-2">
                            <motion.span
                              className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                              animate={{ opacity: [0.4, 1, 0.4] }}
                              transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                delay: 0,
                              }}
                            />
                            <motion.span
                              className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                              animate={{ opacity: [0.4, 1, 0.4] }}
                              transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                delay: 0.2,
                              }}
                            />
                            <motion.span
                              className="w-1.5 h-1.5 bg-gray-400 rounded-full"
                              animate={{ opacity: [0.4, 1, 0.4] }}
                              transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                delay: 0.4,
                              }}
                            />
                          </span>
                        )}
                      </div>

                      {/* Message Actions Row (Copy, Like, Dislike, Share, Read aloud, Regenerate) */}
                      {!isGenerating && (
                        <MessageActions
                          content={msg.content}
                          provider={msg.provider}
                          onRegenerate={
                            onRegenerate ? () => onRegenerate(idx) : null
                          }
                        />
                      )}
                    </>
                  )}
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Lightbox Zoom Modal — image only, dark backdrop, no white frame */}
      <AnimatePresence>
        {activeZoom && (
          <ZoomModal activeZoom={activeZoom} setActiveZoom={setActiveZoom} />
        )}
      </AnimatePresence>
    </div>
  );
}
