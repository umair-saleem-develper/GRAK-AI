"use client";
import React, { useState, useRef, useEffect } from "react";
import {
  Plus,
  Mic,
  ArrowUp,
  Square,
  FileText,
  X,
  Loader2,
  Paperclip,
  Cloud,
  Search,
  LayoutGrid,
  Share2,
  ChevronRight,
  ChevronLeft,
  Trash2,
  Globe,
  Sparkles,
  Image as ImageIcon,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchWithAuth } from "@/lib/apiClient";
import { useQueryClient } from "@tanstack/react-query";
import ComposerActions from "./ComposerActions";

export function VoiceOrbIndicator({
  voiceState = "listening",
  isMuted = false,
}) {
  const isSpeaking = voiceState === "speaking" && !isMuted;

  return (
    <div className="flex items-center gap-4">
      <style>{`
        @keyframes orbFastSwirl {
          0% { transform: rotate(0deg) scale(1.02); }
          50% { transform: rotate(180deg) scale(1.16); }
          100% { transform: rotate(360deg) scale(1.02); }
        }
        @keyframes orbFastCore {
          0% { transform: rotate(360deg) scale(1.12); }
          50% { transform: rotate(180deg) scale(0.88); }
          100% { transform: rotate(0deg) scale(1.12); }
        }
        @keyframes orbSlowSwirl {
          0% { transform: rotate(0deg) scale(0.98); }
          50% { transform: rotate(180deg) scale(1.04); }
          100% { transform: rotate(360deg) scale(0.98); }
        }
        @keyframes orbSlowCore {
          0% { transform: rotate(360deg) scale(1); }
          50% { transform: rotate(180deg) scale(0.94); }
          100% { transform: rotate(0deg) scale(1); }
        }
        .orb-anim-fast-1 { animation: orbFastSwirl 1.25s linear infinite; }
        .orb-anim-fast-2 { animation: orbFastCore 1.7s ease-in-out infinite; }
        .orb-anim-slow-1 { animation: orbSlowSwirl 6.5s linear infinite; }
        .orb-anim-slow-2 { animation: orbSlowCore 8.0s ease-in-out infinite; }
      `}</style>

      {/* Big 3D Gol Daira (Orb) on the Left */}
      <div className="relative w-12 h-12 sm:w-14 sm:h-14 flex items-center justify-center shrink-0">
        {/* Outer Glow Ring */}
        <div
          className={`absolute -inset-1 rounded-full blur-md transition-opacity duration-500 ${
            isSpeaking
              ? "bg-gradient-to-tr from-purple-600 via-fuchsia-400 to-white opacity-75 animate-pulse"
              : "bg-gradient-to-tr from-purple-700 via-indigo-500 to-purple-300 opacity-35"
          }`}
        />

        {/* 3D Sphere Container */}
        <div className="relative w-12 h-12 sm:w-14 sm:h-14 rounded-full overflow-hidden bg-[#090614] border border-white/20 shadow-inner">
          {/* Layer 1: Swirling Purple, White & Dark Gradient */}
          <div
            className={`absolute -inset-3 rounded-full ${
              isSpeaking ? "orb-anim-fast-1" : "orb-anim-slow-1"
            }`}
            style={{
              background: isSpeaking
                ? "conic-gradient(from 0deg, #090614 0deg, #6D28D9 70deg, #FFFFFF 135deg, #A855F7 210deg, #1E1B4B 280deg, #F3E8FF 330deg, #090614 360deg)"
                : "conic-gradient(from 0deg, #090614 0deg, #4C1D95 85deg, #E9D5FF 155deg, #7C3AED 230deg, #111827 305deg, #C4B5FD 340deg, #090614 360deg)",
              filter: "blur(4px)",
            }}
          />

          {/* Layer 2: Counter-Rotating 3D Core */}
          <div
            className={`absolute -inset-2 rounded-full mix-blend-screen ${
              isSpeaking ? "orb-anim-fast-2" : "orb-anim-slow-2"
            }`}
            style={{
              background:
                "radial-gradient(circle at 32% 30%, rgba(255,255,255,0.95) 0%, rgba(168,85,247,0.82) 42%, rgba(9,6,20,0.92) 78%)",
              filter: "blur(2.5px)",
            }}
          />

          {/* Layer 3: 3D Spherical Light & Shadow Shading */}
          <div
            className="absolute inset-0 rounded-full pointer-events-none"
            style={{
              background:
                "radial-gradient(circle at 30% 24%, rgba(255,255,255,0.55) 0%, rgba(255,255,255,0.08) 34%, transparent 65%)",
              boxShadow: "inset 0 -5px 10px rgba(5, 4, 12, 0.9)",
            }}
          />
        </div>
      </div>

      {/* Status Text: "Listening", "Thinking...", "Speaking", "Muted" */}
      <span className="text-[20px] sm:text-[22px] font-bold text-white tracking-tight select-none">
        {isMuted
          ? "Muted"
          : voiceState === "thinking"
            ? "Thinking..."
            : isSpeaking
              ? "Speaking"
              : "Listening"}
      </span>
    </div>
  );
}

export default function MessageInput({
  onSendMessage,
  isGenerating,
  onStop,
  isEmpty,
  editingImage = null,
  onClearEditingImage = null,
}) {
  const [content, setContent] = useState("");
  const [isCreateImageMode, setIsCreateImageMode] = useState(false);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [toastMessage, setToastMessage] = useState(null);
  const recognitionRef = useRef(null);

  // Grak Speak Voice Mode States
  const [isVoiceActive, setIsVoiceActive] = useState(false);
  const [voiceState, setVoiceState] = useState("listening"); // "listening" | "speaking"
  const [isVoiceMuted, setIsVoiceMuted] = useState(false);
  const voiceRecognitionRef = useRef(null);
  const isVoiceMutedRef = useRef(false);
  useEffect(() => {
    isVoiceMutedRef.current = isVoiceMuted;
  }, [isVoiceMuted]);

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [menuSubView, setMenuSubView] = useState("main"); // "main" | "projects" | "connectors"
  const [menuSearch, setMenuSearch] = useState("");
  const [newProjectName, setNewProjectName] = useState("");
  const [projects, setProjects] = useState([]);
  const [connectors, setConnectors] = useState([
    {
      id: "drive",
      name: "Google Drive",
      desc: "Cloud files & Google Docs",
      connected: true,
      icon: "cloud",
    },
    {
      id: "github",
      name: "GitHub",
      desc: "Repositories & commits",
      connected: false,
      icon: "code",
    },
    {
      id: "notion",
      name: "Notion",
      desc: "Workspace pages & notes",
      connected: false,
      icon: "file",
    },
    {
      id: "web",
      name: "Live Web Search",
      desc: "Real-time internet access",
      connected: true,
      icon: "globe",
    },
  ]);
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const [uploadError, setUploadError] = useState(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  const placeholders = [
    "How can I help you today?",
    "What's on your mind?",
    "Ask Grak",
  ];

  // Load projects from localStorage and sync across components
  useEffect(() => {
    const loadProjects = () => {
      try {
        const stored = localStorage.getItem("grak_projects");
        if (stored) setProjects(JSON.parse(stored));
        else setProjects([]);
      } catch (err) {
        console.warn(err);
      }
    };
    loadProjects();

    const handleCreated = () => loadProjects();
    const handleDeleted = () => loadProjects();

    window.addEventListener("grak-project-created", handleCreated);
    window.addEventListener("grak-project-deleted", handleDeleted);
    window.addEventListener("storage", loadProjects);

    return () => {
      window.removeEventListener("grak-project-created", handleCreated);
      window.removeEventListener("grak-project-deleted", handleDeleted);
      window.removeEventListener("storage", loadProjects);
    };
  }, []);

  // Focus composer automatically when user clicks "Edit" on a generated image
  useEffect(() => {
    if (editingImage?.url) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 50);
    }
  }, [editingImage]);

  // Listen for activate-create-image-mode from Sidebar or elsewhere
  useEffect(() => {
    const handleActivate = () => {
      setIsCreateImageMode(true);
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 50);
    };
    window.addEventListener("activate-create-image-mode", handleActivate);
    return () =>
      window.removeEventListener("activate-create-image-mode", handleActivate);
  }, []);

  const handleCreateProject = () => {
    if (!newProjectName.trim()) return;
    const newProj = {
      id: "proj_" + Date.now(),
      name: newProjectName.trim(),
      createdAt: new Date().toISOString(),
    };
    const updated = [newProj, ...projects];
    setProjects(updated);
    try {
      localStorage.setItem("grak_projects", JSON.stringify(updated));
    } catch (e) {
      console.warn(e);
    }
    window.dispatchEvent(
      new CustomEvent("grak-project-created", { detail: newProj }),
    );
    window.dispatchEvent(new CustomEvent("open-sidebar"));
    setNewProjectName("");
  };

  const handleDeleteProject = (projId) => {
    const updated = projects.filter((p) => p.id !== projId);
    setProjects(updated);
    try {
      localStorage.setItem("grak_projects", JSON.stringify(updated));
    } catch (e) {
      console.warn(e);
    }
    window.dispatchEvent(
      new CustomEvent("grak-project-deleted", { detail: { id: projId } }),
    );
  };

  const handleToggleConnector = (id) => {
    setConnectors((prev) =>
      prev.map((c) => (c.id === id ? { ...c, connected: !c.connected } : c)),
    );
  };

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex((prev) => (prev + 1) % placeholders.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    // Reset height first so scrollHeight reflects natural content height
    el.style.height = "auto";
    const next = Math.max(36, Math.min(el.scrollHeight, 200));
    el.style.height = `${next}px`;
    // Enable internal scroll only when we've hit the 200px cap
    el.style.overflowY = el.scrollHeight > 200 ? "auto" : "hidden";
  }, [content]);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        isMenuOpen &&
        !e.target.closest(".upload-menu-container") &&
        !e.target.closest(".upload-toggle-btn")
      ) {
        setIsMenuOpen(false);
        setMenuSubView("main");
        setMenuSearch("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isMenuOpen]);

  // Speech to text / dictation handler
  const handleMic = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setToastMessage("Speech recognition not supported in this browser");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          setContent((prev) =>
            prev ? `${prev.trim()} ${transcript}` : transcript,
          );
        }
      };

      recognition.onerror = (err) => {
        console.warn("Speech recognition error:", err);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Could not start speech recognition:", err);
      setIsListening(false);
    }
  };

  // ─── Grak Speak Voice Mode Engine ──────────────────────────────────────
  const queryClient = useQueryClient();
  const voiceSocketRef = useRef(null);
  const audioContextRef = useRef(null);
  const currentAudioSourceRef = useRef(null);
  const speechRecognitionRef = useRef(null);
  const isVoiceActiveRef = useRef(false);

  const stopAudioPlayback = () => {
    if (currentAudioSourceRef.current) {
      try {
        currentAudioSourceRef.current.stop();
        currentAudioSourceRef.current.disconnect();
      } catch (e) {}
      currentAudioSourceRef.current = null;
    }
  };

  const playBase64Audio = async (base64Audio) => {
    try {
      stopAudioPlayback();
      const binaryString = window.atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      const audioCtx = audioContextRef.current || new AudioCtxClass();
      audioContextRef.current = audioCtx;

      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      const audioBuffer = await audioCtx.decodeAudioData(bytes.buffer);
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      currentAudioSourceRef.current = source;

      setVoiceState("speaking");

      source.onended = () => {
        setVoiceState("listening");
        currentAudioSourceRef.current = null;
        if (
          voiceSocketRef.current &&
          voiceSocketRef.current.readyState === WebSocket.OPEN
        ) {
          voiceSocketRef.current.send(
            JSON.stringify({ type: "playback_finished" }),
          );
        }
      };

      source.start(0);
    } catch (err) {
      console.warn("Audio playback error:", err);
      setVoiceState("listening");
    }
  };

  // Sync spoken turn into active chat conversation cache
  const syncTurnToChat = (userText, aiText) => {
    try {
      const params =
        typeof window !== "undefined"
          ? new URLSearchParams(window.location.search)
          : null;
      const convId = params ? params.get("c") : null;
      const newMsgs = [];
      if (userText) {
        newMsgs.push({
          id: `user_voice_${Date.now()}`,
          role: "user",
          content: userText,
        });
      }
      if (aiText) {
        newMsgs.push({
          id: `asst_voice_${Date.now() + 1}`,
          role: "assistant",
          content: aiText,
          provider: "groq",
          isVoice: true,
        });
      }

      if (convId && newMsgs.length > 0) {
        queryClient.setQueryData(["conversation", convId], (old) => {
          if (!old) return { messages: newMsgs };
          return { ...old, messages: [...old.messages, ...newMsgs] };
        });
      }

      // Also dispatch event for any other listeners
      window.dispatchEvent(
        new CustomEvent("grak-voice-turn", {
          detail: { userText, aiText, conversationId: convId },
        }),
      );
    } catch (e) {
      console.warn("Could not sync voice turn to chat:", e);
    }
  };

  const handleBargeIn = () => {
    stopAudioPlayback();
    if (
      voiceSocketRef.current &&
      voiceSocketRef.current.readyState === WebSocket.OPEN
    ) {
      voiceSocketRef.current.send(JSON.stringify({ type: "barge_in" }));
    }
    setVoiceState("listening");
  };

  const startVoiceMode = async () => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setToastMessage(
        "Speech recognition is not supported in this browser. Please use Chrome or Edge.",
      );
      return;
    }

    setIsVoiceActive(true);
    isVoiceActiveRef.current = true;
    setVoiceState("listening");
    setIsVoiceMuted(false);

    try {
      // 1. Initialize AudioContext early for smooth playback
      const AudioCtxClass = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtxClass();
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }
      audioContextRef.current = audioCtx;

      // 2. Connect WebSocket to FastAPI backend
      let wsUrl = process.env.NEXT_PUBLIC_WS_URL;
      if (!wsUrl) {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (apiUrl && !apiUrl.includes("localhost") && !apiUrl.includes("127.0.0.1")) {
          try {
            const parsed = new URL(apiUrl);
            const proto = parsed.protocol === "https:" ? "wss:" : "ws:";
            wsUrl = `${proto}//${parsed.host}/api/voice/grak-speak`;
          } catch (e) {
            const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
            const wsHost = window.location.hostname || "localhost";
            wsUrl = `${wsProtocol}//${wsHost}:8001/api/voice/grak-speak`;
          }
        } else {
          const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
          const wsHost = window.location.hostname || "localhost";
          wsUrl = `${wsProtocol}//${wsHost}:8001/api/voice/grak-speak`;
        }
      }

      const ws = new WebSocket(wsUrl);
      voiceSocketRef.current = ws;

      ws.onopen = () => {
        setVoiceState("listening");
      };

      ws.onmessage = async (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "state" && msg.voiceState) {
            setVoiceState(msg.voiceState);
          } else if (msg.type === "response") {
            // Sync user speech & assistant reply to chat conversation
            syncTurnToChat(msg.userText, msg.text);
          } else if (msg.type === "audio") {
            if (msg.audio) {
              await playBase64Audio(msg.audio);
            }
          } else if (
            msg.type === "playback_done" ||
            msg.type === "interrupted"
          ) {
            stopAudioPlayback();
            setVoiceState("listening");
          } else if (msg.type === "ping") {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(JSON.stringify({ type: "pong" }));
            }
          } else if (msg.type === "error") {
            console.warn("Voice agent error:", msg.message);
            setToastMessage(msg.message || "Voice session error");
          }
        } catch (e) {
          console.warn("Error parsing voice WS message:", e);
        }
      };

      ws.onerror = (e) => {
        console.warn("Voice WebSocket error:", e);
      };

      ws.onclose = () => {
        if (isVoiceActiveRef.current) {
          stopVoiceMode();
        }
      };

      // 3. Initialize continuous SpeechRecognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onspeechstart = () => {
        // If agent is speaking, barge-in immediately
        if (currentAudioSourceRef.current) {
          handleBargeIn();
        }
      };

      recognition.onresult = (event) => {
        if (isVoiceMutedRef.current) return;

        // Barge-in check: user is producing speech
        if (currentAudioSourceRef.current) {
          handleBargeIn();
        }

        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const trans = event.results[i][0]?.transcript || "";
          if (event.results[i].isFinal) {
            finalTranscript += trans;
          } else {
            interimTranscript += trans;
          }
        }

        const finalText = finalTranscript.trim();
        if (finalText && ws.readyState === WebSocket.OPEN) {
          setVoiceState("thinking");
          ws.send(
            JSON.stringify({
              type: "transcript",
              text: finalText,
              isFinal: true,
            }),
          );
        }
      };

      recognition.onerror = (err) => {
        if (err.error !== "no-speech") {
          console.warn("Speech recognition error:", err.error);
        }
      };

      recognition.onend = () => {
        // Keep listening across multiple turns without interruption
        if (isVoiceActiveRef.current && !isVoiceMutedRef.current) {
          try {
            recognition.start();
          } catch (e) {}
        }
      };

      speechRecognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Voice mode initialization failed:", err);
      setToastMessage("Microphone permission required for voice mode");
      stopVoiceMode();
    }
  };

  const stopVoiceMode = () => {
    isVoiceActiveRef.current = false;
    stopAudioPlayback();

    if (speechRecognitionRef.current) {
      try {
        speechRecognitionRef.current.onend = null;
        speechRecognitionRef.current.stop();
      } catch (e) {}
      speechRecognitionRef.current = null;
    }

    if (voiceSocketRef.current) {
      voiceSocketRef.current.onclose = null;
      try {
        if (voiceSocketRef.current.readyState === WebSocket.OPEN) {
          voiceSocketRef.current.send(JSON.stringify({ type: "close" }));
        }
        voiceSocketRef.current.close();
      } catch (e) {}
      voiceSocketRef.current = null;
    }

    if (audioContextRef.current) {
      try {
        audioContextRef.current.close();
      } catch (e) {}
      audioContextRef.current = null;
    }

    setIsVoiceActive(false);
    setVoiceState("listening");
    setIsVoiceMuted(false);
  };

  const toggleVoiceMute = () => {
    setIsVoiceMuted((prev) => {
      const next = !prev;
      if (next) {
        stopAudioPlayback();
        if (speechRecognitionRef.current) {
          try {
            speechRecognitionRef.current.stop();
          } catch (e) {}
        }
        if (
          voiceSocketRef.current &&
          voiceSocketRef.current.readyState === WebSocket.OPEN
        ) {
          voiceSocketRef.current.send(JSON.stringify({ type: "barge_in" }));
        }
      } else {
        if (speechRecognitionRef.current && isVoiceActiveRef.current) {
          try {
            speechRecognitionRef.current.start();
          } catch (e) {}
        }
      }
      return next;
    });
  };

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      stopVoiceMode();
    };
  }, []);

  const handleVoice = () => {
    startVoiceMode();
  };

  useEffect(() => {
    if (!toastMessage) return;
    const t = setTimeout(() => setToastMessage(null), 3000);
    return () => clearTimeout(t);
  }, [toastMessage]);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;
    setUploadError(null);
    setFile(selectedFile);
  };

  const clearFile = () => {
    setFile(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (e) => {
    if (e && typeof e.preventDefault === "function") {
      e.preventDefault();
    }
    if ((!content.trim() && !file) || isGenerating || isUploading) return;

    let uploadedText = null;
    let imageBase64 = null;

    if (file) {
      setIsUploading(true);
      setUploadError(null);

      // Convert image to base64 for direct inline vision transmission to Gemini
      const isImage =
        file.type?.startsWith("image/") ||
        /\.(png|jpe?g|webp|gif|bmp)$/i.test(file.name);
      if (isImage) {
        try {
          imageBase64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.onerror = () => resolve(null);
            reader.readAsDataURL(file);
          });
        } catch (readErr) {
          console.warn("Could not read file locally as base64:", readErr);
        }
      }

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetchWithAuth("/api/uploads", {
          method: "POST",
          body: formData,
        });

        if (response && response.ok) {
          const data = await response.json();
          uploadedText = data.extracted_text || data.text || "";
          if (data.image_base64) {
            imageBase64 = data.image_base64;
          }
        } else {
          // Requirement 3: If extraction really fails, do not send placeholder to chat; show clear UI error
          const errData = await response?.json().catch(() => ({}));
          const errMsg = errData?.detail || "Could not read this image";
          setUploadError(errMsg);
          setIsUploading(false);
          return;
        }
      } catch (err) {
        // Requirement 3: If extraction fails, show clear UI error and abort message send
        setUploadError("Could not read this image");
        setIsUploading(false);
        return;
      } finally {
        setIsUploading(false);
      }
    }

    const effectiveMode =
      isCreateImageMode || Boolean(editingImage?.url) ? "create_image" : null;
    onSendMessage(
      content,
      uploadedText,
      imageBase64,
      effectiveMode,
      editingImage?.url || null,
    );
    setContent("");
    setIsCreateImageMode(false);
    onClearEditingImage?.();
    clearFile();
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Escape" && editingImage?.url) {
      e.preventDefault();
      onClearEditingImage?.();
      return;
    }
    if (e.key === "Escape" && isCreateImageMode) {
      e.preventDefault();
      setIsCreateImageMode(false);
      return;
    }
    if (e.key === "Backspace" && isCreateImageMode && !content) {
      e.preventDefault();
      setIsCreateImageMode(false);
      return;
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="w-full relative z-20 group">
      {/* Upload & Workspace Menu - Matching Image 2 */}
      {isMenuOpen && (
        <div className="absolute bottom-full left-0 mb-3 w-[290px] bg-[#1a1921]/95 dark:bg-[#121118]/95 backdrop-blur-2xl border border-black/10 dark:border-white/10 rounded-2xl shadow-[0_12px_40px_rgba(0,0,0,0.6)] py-2 z-50 animate-in fade-in zoom-in-95 slide-in-from-bottom-2 upload-menu-container text-gray-800 dark:text-gray-200">
          {menuSubView === "main" && (
            <div className="px-1.5 space-y-1">
              {/* Search Bar */}
              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10 text-gray-400 focus-within:text-white focus-within:border-white/30 transition-colors mx-1 mb-2">
                <Search size={15} className="shrink-0" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={menuSearch}
                  onChange={(e) => setMenuSearch(e.target.value)}
                  className="w-full bg-transparent text-[13px] text-gray-900 dark:text-white placeholder-gray-400 outline-none"
                  autoFocus
                />
              </div>

              {/* Projects Item */}
              {("projects".includes(menuSearch.toLowerCase()) ||
                !menuSearch) && (
                <button
                  type="button"
                  onClick={() => setMenuSubView("projects")}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <LayoutGrid
                      size={18}
                      className="text-gray-400 group-hover:text-white transition-colors"
                    />
                    <span>Projects</span>
                  </div>
                  <ChevronRight
                    size={15}
                    className="text-gray-400 group-hover:text-white transition-colors"
                  />
                </button>
              )}

              {/* Connectors Item */}
              {("connectors".includes(menuSearch.toLowerCase()) ||
                !menuSearch) && (
                <button
                  type="button"
                  onClick={() => {
                    setIsMenuOpen(false);
                    window.dispatchEvent(new CustomEvent("open-connectors"));
                  }}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Share2
                      size={18}
                      className="text-gray-400 group-hover:text-white transition-colors"
                    />
                    <span>Connectors</span>
                  </div>
                  <ChevronRight
                    size={15}
                    className="text-gray-400 group-hover:text-white transition-colors"
                  />
                </button>
              )}

              {/* Create image Item */}
              {("create image".includes(menuSearch.toLowerCase()) ||
                !menuSearch) && (
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateImageMode(true);
                    setIsMenuOpen(false);
                    setTimeout(() => {
                      textareaRef.current?.focus();
                    }, 50);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Sparkles
                      size={18}
                      className="text-gray-400 group-hover:text-blue-400 transition-colors"
                    />
                    <span>Create image</span>
                  </div>
                </button>
              )}

              {/* Attach files Item */}
              {("attach files".includes(menuSearch.toLowerCase()) ||
                !menuSearch) && (
                <button
                  type="button"
                  onClick={() => {
                    fileInputRef.current?.click();
                    setIsMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium text-gray-800 dark:text-gray-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <Paperclip
                      size={18}
                      className="text-gray-400 group-hover:text-white transition-colors"
                    />
                    <span>Attach files</span>
                  </div>
                </button>
              )}
            </div>
          )}

          {menuSubView === "projects" && (
            <div className="px-2 space-y-2">
              {/* Header */}
              <div className="flex items-center justify-between pb-2 border-b border-black/5 dark:border-white/10">
                <button
                  type="button"
                  onClick={() => setMenuSubView("main")}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors p-1 rounded-md cursor-pointer"
                >
                  <ChevronLeft size={16} />
                  <span>Back</span>
                </button>
                <span className="text-xs font-semibold text-gray-900 dark:text-white flex items-center gap-1.5">
                  <LayoutGrid size={14} className="text-white" /> Projects
                </span>
                <span className="text-[10px] bg-white/10 text-gray-300 px-1.5 py-0.5 rounded-full font-mono">
                  {projects.length}
                </span>
              </div>

              {/* Create Input */}
              <div className="space-y-1.5 pt-1">
                <div className="flex items-center gap-1.5">
                  <input
                    type="text"
                    placeholder="Enter project name..."
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleCreateProject();
                      }
                    }}
                    className="flex-1 bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10 rounded-xl px-3 py-2 text-xs text-gray-900 dark:text-white placeholder-gray-400 outline-none focus:border-white/30 transition-colors"
                    autoFocus
                  />
                  <button
                    type="button"
                    onClick={handleCreateProject}
                    disabled={!newProjectName.trim()}
                    className="bg-white hover:bg-gray-200 disabled:opacity-40 text-black text-xs font-semibold px-3 py-2 rounded-xl transition-all shrink-0 cursor-pointer shadow-sm"
                  >
                    + Create
                  </button>
                </div>
                <p className="text-[10px] text-gray-400 dark:text-gray-500 px-1">
                  Projects automatically show in the left sidebar.
                </p>
              </div>

              {/* Existing Projects List */}
              <div className="max-h-44 overflow-y-auto space-y-1 pt-1.5 scrollbar-thin">
                {projects.length === 0 ? (
                  <div className="text-[11px] text-gray-400 dark:text-gray-500 text-center py-4 italic">
                    No projects yet. Type a name above to create your first
                    project!
                  </div>
                ) : (
                  projects.map((proj) => (
                    <div
                      key={proj.id}
                      className="flex items-center justify-between px-2.5 py-1.5 rounded-xl text-xs bg-black/5 dark:bg-white/5 hover:bg-white/10 text-gray-800 dark:text-gray-200 group border border-transparent hover:border-white/10 transition-all"
                    >
                      <div className="flex items-center gap-2 truncate min-w-0">
                        <LayoutGrid
                          size={13}
                          className="text-gray-400 group-hover:text-white shrink-0"
                        />
                        <span className="truncate font-medium">
                          {proj.name}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteProject(proj.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 p-1 rounded transition-opacity cursor-pointer"
                        title="Delete project"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {menuSubView === "connectors" && (
            <div className="px-2 space-y-2">
              {/* Header */}
              <div className="flex items-center justify-between pb-2 border-b border-black/5 dark:border-white/10">
                <button
                  type="button"
                  onClick={() => setMenuSubView("main")}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-800 dark:hover:text-white transition-colors p-1 rounded-md cursor-pointer"
                >
                  <ChevronLeft size={16} />
                  <span>Back</span>
                </button>
                <span className="text-xs font-semibold text-gray-900 dark:text-white flex items-center gap-1.5">
                  <Share2 size={14} className="text-white" /> Connectors
                </span>
                <span className="text-[10px] text-gray-400">Integration</span>
              </div>

              {/* Connectors List */}
              <div className="space-y-1.5 pt-1 max-h-52 overflow-y-auto scrollbar-thin">
                {connectors.map((c) => (
                  <div
                    key={c.id}
                    className="flex items-center justify-between p-2 rounded-xl bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/10 hover:border-white/20 transition-all text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${c.connected ? "bg-white/15 text-white border border-white/20" : "bg-black/10 dark:bg-white/10 text-gray-400"}`}
                      >
                        {c.icon === "cloud" && <Cloud size={14} />}
                        {c.icon === "code" && <FileText size={14} />}
                        {c.icon === "file" && <FileText size={14} />}
                        {c.icon === "globe" && <Globe size={14} />}
                      </div>
                      <div className="flex flex-col min-w-0">
                        <span className="font-medium text-gray-900 dark:text-white truncate">
                          {c.name}
                        </span>
                        <span className="text-[10px] text-gray-400 truncate">
                          {c.desc}
                        </span>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleToggleConnector(c.id)}
                      className={`px-2 py-1 rounded-lg text-[10px] font-semibold transition-all shrink-0 cursor-pointer ${
                        c.connected
                          ? "bg-white/15 text-white border border-white/20 hover:bg-white/25"
                          : "bg-black/10 dark:bg-white/10 text-gray-400 hover:text-white hover:bg-black/20 dark:hover:bg-white/20"
                      }`}
                    >
                      {c.connected ? "Active" : "Connect"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Attached file preview */}
      {file && (
        <div className="absolute bottom-full left-4 mb-3 flex items-center gap-3 bg-gray-100 dark:bg-[#1e1e1e] border border-black/10 dark:border-white/10 px-4 py-2 rounded-xl shadow-lg animate-in fade-in slide-in-from-bottom-2">
          <div
            className={`p-2 rounded-lg ${file.type?.startsWith("image/") || /\.(png|jpe?g|webp|gif|bmp)$/i.test(file.name) ? "bg-blue-500/20 text-blue-400" : "bg-purple-500/20 text-purple-400"}`}
          >
            {file.type?.startsWith("image/") ||
            /\.(png|jpe?g|webp|gif|bmp)$/i.test(file.name) ? (
              <ImageIcon size={20} />
            ) : (
              <FileText size={20} />
            )}
          </div>
          <div className="flex flex-col min-w-0 pr-4">
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate max-w-[200px]">
              {file.name}
            </span>
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </div>
          <button
            type="button"
            onClick={clearFile}
            className="text-gray-400 dark:text-gray-500 dark:text-gray-400 hover:text-black dark:text-white p-1 rounded-full hover:bg-black/10 dark:bg-white/10 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Clear error alert in UI (Requirement 3: Could not read this image) */}
      {uploadError && (
        <div className="absolute bottom-full left-4 mb-3 flex items-center gap-2.5 bg-red-500/10 border border-red-500/30 text-red-600 dark:text-red-400 px-4 py-2 rounded-xl text-xs font-medium shadow-md animate-in fade-in slide-in-from-bottom-2">
          <span>{uploadError}</span>
          <button
            type="button"
            onClick={() => setUploadError(null)}
            className="hover:opacity-80 p-0.5 rounded-full hover:bg-red-500/20 transition-colors"
            title="Dismiss error"
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Toast alert */}
      {toastMessage && (
        <div className="absolute bottom-full right-4 mb-3 flex items-center gap-2 bg-[#1f1e24] border border-white/10 text-white px-3.5 py-1.5 rounded-full text-xs font-medium shadow-lg animate-in fade-in slide-in-from-bottom-2 z-50">
          <span>{toastMessage}</span>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          backgroundColor: "var(--composer-bg, #14131a)",
          borderColor: "var(--composer-border, rgba(255, 255, 255, 0.12))",
        }}
        className={`relative flex flex-col justify-between border rounded-3xl transition-all shadow-none focus-within:border-white/25 ${
          isVoiceActive ? "p-2 min-h-[68px] justify-center" : "pt-2.5 px-4 pb-2"
        }`}
      >
        <input
          type="file"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".txt,.pdf,.docx,.doc,.png,.jpg,.jpeg,.webp,.gif,.bmp"
        />

        {/* VOICE BAR MODE: isVoiceActive === true */}
        {isVoiceActive ? (
          <div className="flex items-center justify-between w-full px-3 py-2 min-h-[68px]">
            {/* Left: 3D Orb + Status Typography */}
            <VoiceOrbIndicator voiceState={voiceState} isMuted={isVoiceMuted} />

            {/* Right Side Controls in Voice Mode */}
            <div className="flex items-center gap-2.5 shrink-0">
              {/* Attachment Button */}
              <button
                type="button"
                onClick={() => {
                  setIsMenuOpen(!isMenuOpen);
                  if (!isMenuOpen) {
                    setMenuSubView("main");
                    setMenuSearch("");
                  }
                }}
                className="w-10 h-10 rounded-full bg-[#1e1c27] hover:bg-[#282635] text-white flex items-center justify-center transition-colors shadow-sm cursor-pointer"
                title="Attach or integrate"
                aria-label="Attach or integrate"
              >
                <Plus size={19} />
              </button>

              {/* Circular Mic Mute/Unmute Toggle Button */}
              <button
                type="button"
                onClick={toggleVoiceMute}
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors shadow-sm cursor-pointer ${
                  isVoiceMuted
                    ? "bg-red-500/20 text-red-400 border border-red-500/30"
                    : "bg-[#2A2937] hover:bg-[#353345] text-white"
                }`}
                title={isVoiceMuted ? "Unmute microphone" : "Mute microphone"}
                aria-label={
                  isVoiceMuted ? "Unmute microphone" : "Mute microphone"
                }
              >
                <Mic
                  size={18}
                  className={isVoiceMuted ? "line-through opacity-70" : ""}
                />
              </button>

              {/* Circular White Close Button */}
              <button
                type="button"
                onClick={stopVoiceMode}
                className="w-10 h-10 rounded-full bg-white text-black hover:bg-gray-200 flex items-center justify-center transition-colors shadow-md cursor-pointer font-bold"
                title="End voice session"
                aria-label="End voice session"
              >
                <X size={19} strokeWidth={2.5} />
              </button>
            </div>
          </div>
        ) : (
          /* NORMAL SEARCH BAR MODE: isVoiceActive === false */
          <>
            {/* Editing target image preview pill */}
            {editingImage?.url && (
              <div className="mb-2 flex items-center justify-between gap-2.5 px-2.5 py-1.5 rounded-2xl bg-purple-500/10 border border-purple-500/30">
                <div className="flex items-center gap-2.5 min-w-0">
                  <img
                    src={editingImage.url}
                    alt="Editing target"
                    className="w-9 h-9 rounded-lg object-cover border border-purple-400/30 shrink-0"
                  />
                  <div className="flex flex-col min-w-0">
                    <span className="text-xs font-semibold text-purple-200 leading-tight">
                      Editing image...
                    </span>
                    {editingImage.prompt && (
                      <span className="text-[11px] text-purple-300/70 truncate max-w-[320px]">
                        {editingImage.prompt}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onClearEditingImage?.();
                    textareaRef.current?.focus();
                  }}
                  className="p-1 rounded-full text-purple-300 hover:text-white hover:bg-purple-500/20 transition-colors cursor-pointer shrink-0"
                  title="Cancel image edit"
                  aria-label="Cancel image edit"
                >
                  <X size={14} />
                </button>
              </div>
            )}

            {/* Top: Input Area */}
            <div className="relative w-full flex flex-wrap items-center gap-2">
              {/* Create image mode chip */}
              {isCreateImageMode && (
                <div
                  style={{
                    borderColor: "var(--chip-color, #3b82f6)",
                    color: "var(--chip-color, #3b82f6)",
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 border transition-all shrink-0 select-none"
                >
                  <span className="flex items-center gap-1">
                    <span>🖼</span>
                    <span>Create image</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setIsCreateImageMode(false);
                      textareaRef.current?.focus();
                    }}
                    className="hover:opacity-75 p-0.5 rounded-full cursor-pointer ml-0.5"
                    aria-label="Remove Create image mode"
                  >
                    <X size={12} />
                  </button>
                </div>
              )}

              <div className="relative flex-1 min-w-[200px] flex items-start">
                <textarea
                  ref={textareaRef}
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={
                    isUploading
                      ? "Uploading file..."
                      : editingImage?.url
                        ? "Describe what you want to change in this image..."
                        : isCreateImageMode
                          ? "Describe the image you want"
                          : isEmpty
                            ? placeholders[placeholderIndex]
                            : "Ask anything"
                  }
                  className="w-full bg-transparent text-white outline-none resize-none scrollbar-thin text-[16px] leading-[24px] relative z-10 m-0 border-0 box-border"
                  style={{
                    fontSize: "16px",
                    lineHeight: "24px",
                    paddingTop: "6px",
                    paddingBottom: "6px",
                    paddingLeft: "0px",
                    paddingRight: "0px",
                    height: "36px",
                    minHeight: "36px",
                    maxHeight: "200px",
                    boxSizing: "border-box",
                    display: "block",
                  }}
                  rows={1}
                  disabled={isGenerating || isUploading}
                />
              </div>
            </div>

            {/* Bottom toolbar row: height ~36px */}
            <div className="flex items-center justify-between h-9 mt-1">
              {/* Left: Plus Button */}
              <button
                type="button"
                onClick={() => {
                  setIsMenuOpen(!isMenuOpen);
                  if (!isMenuOpen) {
                    setMenuSubView("main");
                    setMenuSearch("");
                  }
                }}
                style={{
                  color: isMenuOpen
                    ? "#ffffff"
                    : "var(--composer-icon, rgba(255, 255, 255, 0.75))",
                }}
                className={`upload-toggle-btn transition-all w-8 h-8 rounded-full shrink-0 flex items-center justify-center ${isMenuOpen ? "bg-white/20" : "hover:text-white hover:bg-white/10"}`}
                title="Attach or integrate"
              >
                <motion.div
                  animate={{ rotate: isMenuOpen ? 45 : 0 }}
                  transition={{ type: "spring", stiffness: 260, damping: 20 }}
                  className="flex items-center justify-center"
                >
                  <Plus size={18} />
                </motion.div>
              </button>

              {/* Right: ComposerActions */}
              {isGenerating ? (
                <div className="flex items-center gap-1.5 shrink-0">
                  <button
                    type="button"
                    onClick={onStop}
                    className="w-9 h-9 flex items-center justify-center rounded-full bg-white/15 text-white hover:bg-white/25 transition-colors shrink-0 shadow-sm"
                    title="Stop generation"
                    aria-label="Stop generation"
                  >
                    <Square size={13} fill="currentColor" />
                  </button>
                </div>
              ) : (
                <ComposerActions
                  hasText={Boolean(content && content.trim().length > 0)}
                  onSend={handleSubmit}
                  onMic={handleMic}
                  onVoice={handleVoice}
                  listening={isListening}
                  busy={isGenerating || isUploading}
                />
              )}
            </div>
          </>
        )}
      </form>
    </div>
  );
}
