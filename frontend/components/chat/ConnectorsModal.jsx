"use client";
import React, { useState, useEffect } from "react";
import {
  X,
  Search,
  Check,
  ExternalLink,
  RefreshCw,
  Shield,
  Github,
  Database,
  Globe,
  FolderGit2,
  HardDrive,
  FileText,
  Layers,
  Cpu,
  Cloud,
  Slack,
  MessageSquare,
  Terminal,
  Zap,
  CheckCircle2,
  Plus,
  Sparkles,
} from "lucide-react";

const INITIAL_CONNECTORS = [
  {
    id: "web-search",
    name: "Live Web Search",
    category: "Search & Knowledge",
    tag: "Built-in",
    description:
      "Search the public web in real time for latest news, documentation, and live data.",
    icon: Globe,
    iconColor: "from-blue-500 to-cyan-400",
    connected: true,
    popular: true,
  },
  {
    id: "github",
    name: "GitHub",
    category: "Developer",
    tag: "Code",
    description:
      "Connect repositories to search code, review pull requests, and debug issues directly.",
    icon: Github,
    iconColor: "from-zinc-400 to-zinc-100",
    connected: false,
    popular: true,
  },
  {
    id: "google-drive",
    name: "Google Drive",
    category: "Storage",
    tag: "Documents",
    description:
      "Access Google Docs, Sheets, PDFs, and team drive files during conversation.",
    icon: HardDrive,
    iconColor: "from-amber-400 to-emerald-400",
    connected: false,
    popular: true,
  },
  {
    id: "notion",
    name: "Notion",
    category: "Productivity",
    tag: "Workspace",
    description:
      "Query Notion pages, meeting notes, project trackers, and internal team wikis.",
    icon: FileText,
    iconColor: "from-stone-300 to-white",
    connected: false,
    popular: true,
  },
  {
    id: "postgres",
    name: "PostgreSQL / Supabase",
    category: "Database",
    tag: "SQL Data",
    description:
      "Run schema introspection and safe analytical queries against your database.",
    icon: Database,
    iconColor: "from-sky-500 to-indigo-500",
    connected: false,
    popular: true,
  },
  {
    id: "slack",
    name: "Slack",
    category: "Collaboration",
    tag: "Chat",
    description:
      "Search workspace conversations, thread discussions, and team knowledge.",
    icon: Slack,
    iconColor: "from-fuchsia-500 to-rose-400",
    connected: false,
    popular: false,
  },
  {
    id: "figma",
    name: "Figma",
    category: "Design",
    tag: "UI/UX",
    description:
      "Inspect component trees, design system tokens, and UI layout wireframes.",
    icon: Layers,
    iconColor: "from-violet-500 to-pink-500",
    connected: false,
    popular: false,
  },
  {
    id: "terminal-cli",
    name: "Local Terminal / CLI",
    category: "Developer",
    tag: "System",
    description:
      "Execute shell scripts, tests, and build commands within sandbox containers.",
    icon: Terminal,
    iconColor: "from-emerald-400 to-teal-500",
    connected: true,
    popular: false,
  },
];

export default function ConnectorsModal({ isOpen, onClose }) {
  const [open, setOpen] = useState(isOpen || false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [connectors, setConnectors] = useState(INITIAL_CONNECTORS);
  const [connectingId, setConnectingId] = useState(null);

  // Sync internal open state with prop
  useEffect(() => {
    if (typeof isOpen === "boolean") setOpen(isOpen);
  }, [isOpen]);

  // Listen for global open-connectors event
  useEffect(() => {
    const handleOpen = () => setOpen(true);
    window.addEventListener("open-connectors", handleOpen);
    return () => window.removeEventListener("open-connectors", handleOpen);
  }, []);

  // Load persistence
  useEffect(() => {
    try {
      const saved = localStorage.getItem("grak_connectors_state");
      if (saved) {
        const parsed = JSON.parse(saved);
        setConnectors((prev) =>
          prev.map((c) => ({
            ...c,
            connected: parsed[c.id] !== undefined ? parsed[c.id] : c.connected,
          })),
        );
      }
    } catch (e) {
      console.warn("Could not load connectors state", e);
    }
  }, []);

  const handleToggle = (id) => {
    setConnectingId(id);
    setTimeout(() => {
      setConnectors((prev) => {
        const next = prev.map((c) =>
          c.id === id ? { ...c, connected: !c.connected } : c,
        );
        try {
          const stateObj = {};
          next.forEach((c) => {
            stateObj[c.id] = c.connected;
          });
          localStorage.setItem(
            "grak_connectors_state",
            JSON.stringify(stateObj),
          );
        } catch (e) {
          console.warn(e);
        }
        return next;
      });
      setConnectingId(null);
    }, 450);
  };

  const handleClose = () => {
    setOpen(false);
    if (onClose) onClose();
  };

  if (!open) return null;

  const categories = [
    "All",
    "Developer",
    "Storage",
    "Productivity",
    "Database",
    "Collaboration",
  ];

  const filtered = connectors.filter((c) => {
    const matchesSearch =
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.description.toLowerCase().includes(search.toLowerCase()) ||
      c.tag.toLowerCase().includes(search.toLowerCase());
    const matchesCategory =
      selectedCategory === "All" || c.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      {/* Modal Container */}
      <div
        className="w-full max-w-4xl max-h-[90vh] bg-[#111016] border border-white/10 rounded-3xl shadow-[0_24px_80px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden text-gray-200 animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="px-6 py-5 border-b border-white/5 flex items-start justify-between bg-[#16151d]/70">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-white/10 text-gray-300 border border-white/10 flex items-center gap-1.5">
                <Sparkles size={11} className="text-white" /> Connectors &
                Integrations
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-semibold text-white tracking-tight">
              Connect External Tools & Data
            </h2>
            <p className="text-xs sm:text-sm text-gray-400 mt-0.5">
              Sync code repos, cloud documents, databases, and APIs directly
              with Grak AI.
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Close"
          >
            <X size={20} />
          </button>
        </div>

        {/* Toolbar: Search and Filter Tabs */}
        <div className="p-4 sm:px-6 border-b border-white/5 bg-[#14131a] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Categories */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition-colors ${
                  selectedCategory === cat
                    ? "bg-white text-black font-semibold shadow-sm"
                    : "text-gray-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Box */}
          <div className="relative w-full sm:w-64">
            <Search
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Search connectors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-gray-500 outline-none focus:border-white/20 transition-colors"
            />
          </div>
        </div>

        {/* Connector Cards Grid */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 grid grid-cols-1 md:grid-cols-2 gap-3.5 scrollbar-thin scrollbar-thumb-white/10">
          {filtered.length === 0 ? (
            <div className="col-span-full py-12 text-center text-gray-500 text-sm">
              No connectors found matching &ldquo;{search}&rdquo;
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon;
              const isBusy = connectingId === item.id;

              return (
                <div
                  key={item.id}
                  className={`relative p-4 rounded-2xl border transition-all flex flex-col justify-between ${
                    item.connected
                      ? "bg-[#181721] border-white/15 shadow-sm"
                      : "bg-[#14131a] border-white/5 hover:border-white/15 hover:bg-[#181721]"
                  }`}
                >
                  {/* Card Top */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-xl bg-gradient-to-br ${item.iconColor} p-[1px] shrink-0 shadow-md flex items-center justify-center`}
                      >
                        <div className="w-full h-full bg-[#121118]/80 backdrop-blur-sm rounded-[11px] flex items-center justify-center">
                          <Icon size={20} className="text-white" />
                        </div>
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-white text-sm">
                            {item.name}
                          </h4>
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-white/5 text-gray-400 border border-white/5 font-mono">
                            {item.tag}
                          </span>
                        </div>
                        <span className="text-[11px] text-gray-400">
                          {item.category}
                        </span>
                      </div>
                    </div>

                    {/* Status Pill */}
                    {item.connected ? (
                      <span className="flex items-center gap-1.5 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Connected
                      </span>
                    ) : (
                      <span className="text-[11px] text-gray-400 bg-white/5 px-2 py-0.5 rounded-full border border-white/5">
                        Available
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-xs text-gray-400 line-clamp-2 mb-4 leading-relaxed">
                    {item.description}
                  </p>

                  {/* Card Actions */}
                  <div className="flex items-center justify-between pt-3 border-t border-white/5">
                    <div className="flex items-center gap-1.5 text-[11px] text-gray-400">
                      <Shield size={12} className="text-gray-400" />
                      <span>Encrypted SSL</span>
                    </div>

                    <button
                      type="button"
                      disabled={isBusy}
                      onClick={() => handleToggle(item.id)}
                      className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
                        item.connected
                          ? "bg-white/10 hover:bg-red-500/10 text-gray-300 hover:text-red-400 border border-white/10"
                          : "bg-white hover:bg-gray-200 text-black font-semibold shadow-sm"
                      }`}
                    >
                      {isBusy ? (
                        <RefreshCw size={13} className="animate-spin" />
                      ) : item.connected ? (
                        <>
                          <Check size={13} />
                          <span>Connected</span>
                        </>
                      ) : (
                        <>
                          <Plus size={13} />
                          <span>Connect</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 border-t border-white/5 bg-[#14131a] flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>End-to-end token security & isolated user credentials</span>
          </div>
          <button
            onClick={handleClose}
            className="px-4 py-1.5 rounded-xl bg-white/10 hover:bg-white/15 text-white font-medium transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
