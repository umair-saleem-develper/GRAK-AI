"use client";
import React, { useState, useMemo, useEffect } from "react";
import Image from "next/image";
import {
  PenSquare,
  Search,
  MessageSquare,
  LayoutGrid,
  ListFilter,
  ChevronDown,
  ChevronRight,
  MoreHorizontal,
  Zap,
  Pin,
  Edit2,
  Trash2,
  LogOut,
  X,
  Plus,
  FolderDot,
  Diamond,
  PanelLeftClose,
  PanelLeft,
  Check,
  Sparkles,
} from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "@/context/AuthContext";
import { fetchWithAuth } from "@/lib/apiClient";
import ConnectorsModal from "@/components/chat/ConnectorsModal";

export default function Sidebar({
  activeConversationId,
  onSelectConversation,
  onNewChat,
  currentView = "chat",
  onSelectView,
  onOpenSearch,
  isMobile,
  onClose,
}) {
  const queryClient = useQueryClient();
  const { session, logout } = useAuth();

  // Active menu dropdown ID
  const [activeMenuId, setActiveMenuId] = useState(null);

  // Connectors modal state
  const [isConnectorsOpen, setIsConnectorsOpen] = useState(false);

  // Projects & Folders state in Sidebar
  const [projects, setProjects] = useState([]);
  const [folders, setFolders] = useState([]);

  // Inline rename state for conversations
  const [renamingConvId, setRenamingConvId] = useState(null);
  const [renameTitle, setRenameTitle] = useState("");

  // User display name & initial
  const userEmail = session?.user?.email || "";
  const userName = userEmail ? userEmail.split("@")[0] : "mainumair177";
  const userInitial = (userEmail ? userEmail.charAt(0) : "M").toUpperCase();

  // Load projects and folders from localStorage
  useEffect(() => {
    const loadItems = () => {
      try {
        const storedProjects = localStorage.getItem("grak_projects");
        setProjects(storedProjects ? JSON.parse(storedProjects) : []);

        const storedFolders = localStorage.getItem("grak_folders");
        setFolders(storedFolders ? JSON.parse(storedFolders) : []);
      } catch (e) {
        console.warn(e);
      }
    };
    loadItems();

    const handleEvent = () => loadItems();
    window.addEventListener("grak-project-created", handleEvent);
    window.addEventListener("grak-project-deleted", handleEvent);
    window.addEventListener("grak-folder-created", handleEvent);
    window.addEventListener("grak-folder-deleted", handleEvent);
    window.addEventListener("storage", loadItems);

    return () => {
      window.removeEventListener("grak-project-created", handleEvent);
      window.removeEventListener("grak-project-deleted", handleEvent);
      window.removeEventListener("grak-folder-created", handleEvent);
      window.removeEventListener("grak-folder-deleted", handleEvent);
      window.removeEventListener("storage", loadItems);
    };
  }, []);

  // Fetch real conversations from DB for logged-in user
  const { data: convData, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      const res = await fetchWithAuth("/api/conversations");
      if (!res.ok) throw new Error("Failed to fetch conversations");
      return res.json();
    },
  });

  const conversations = convData?.items || convData?.conversations || [];

  // Context menu click
  const handleMenuClick = (e, id) => {
    e.stopPropagation();
    setActiveMenuId(activeMenuId === id ? null : id);
  };

  // Delete conversation
  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    setActiveMenuId(null);
    try {
      const res = await fetchWithAuth(`/api/conversations/${convId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        queryClient.invalidateQueries(["conversations"]);
        if (activeConversationId === convId) {
          onNewChat();
        }
      }
    } catch (err) {
      console.warn("Delete conversation error:", err);
    }
  };

  // Pin/Unpin conversation
  const handleTogglePinConversation = async (convId, currentPinned, e) => {
    e.stopPropagation();
    setActiveMenuId(null);
    try {
      const res = await fetchWithAuth(`/api/conversations/${convId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_pinned: !currentPinned }),
      });
      if (res.ok) {
        queryClient.invalidateQueries(["conversations"]);
      }
    } catch (err) {
      console.warn("Pin error:", err);
    }
  };

  // Save renamed title
  const handleSaveRename = async (convId, e) => {
    if (e) e.stopPropagation();
    if (!renameTitle.trim()) {
      setRenamingConvId(null);
      return;
    }
    try {
      const res = await fetchWithAuth(`/api/conversations/${convId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: renameTitle.trim() }),
      });
      if (res.ok) {
        queryClient.invalidateQueries(["conversations"]);
      }
    } catch (err) {
      console.warn("Rename error:", err);
    }
    setRenamingConvId(null);
    setRenameTitle("");
  };

  const totalProjectsCount = projects.length + folders.length;

  return (
    <>
      <motion.aside
        initial={{ width: 0, opacity: 0 }}
        animate={{ width: 260, opacity: 1 }}
        exit={{ width: 0, opacity: 0 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        className="h-full bg-[#0c0b10] shrink-0 border-r border-white/5 select-none overflow-hidden flex flex-col text-gray-200 fixed md:relative inset-y-0 left-0 z-50 shadow-2xl md:shadow-none"
      >
        <div className="w-[260px] h-full flex flex-col p-3">
          {/* Top Logo Button - OmniAI Logo matching header size that transitions to Close Icon on hover */}
          <div className="flex items-center px-1 pt-1 pb-3">
            <button
              type="button"
              onClick={onClose}
              className="relative group p-1.5 rounded-xl hover:bg-white/10 transition-colors flex items-center justify-center w-10 h-10 shrink-0 cursor-pointer"
              title="Close sidebar"
            >
              {/* OmniAI / Grak Logo - visible normally, hides on hover */}
              <div className="w-10 h-10 flex items-center justify-center transition-opacity duration-200 group-hover:opacity-0 absolute inset-0 m-auto">
                <Image
                  src="/grak-logo-dark.png"
                  alt="OmniAI Logo"
                  width={96}
                  height={96}
                  className="object-contain scale-125 drop-shadow-md"
                  priority
                />
              </div>

              {/* Close Icon - hidden normally, shows on hover */}
              <div className="w-10 h-10 absolute inset-0 m-auto flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 text-gray-300">
                <PanelLeftClose size={22} />
              </div>
            </button>
          </div>

          {/* Action Items List */}
          <div className="space-y-0.5 mb-3">
            {/* 1. New (Pill button) */}
            <button
              type="button"
              onClick={() => {
                if (onSelectView) onSelectView("chat");
                onNewChat();
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl bg-[#23222a] hover:bg-white/15 text-white text-xs font-medium transition-all shadow-sm cursor-pointer group"
            >
              <PenSquare size={15} className="text-white shrink-0" />
              <span>New</span>
            </button>

            {/* Create image */}
            <button
              type="button"
              onClick={() => {
                if (onSelectView) onSelectView("chat");
                if (!activeConversationId) {
                  onNewChat();
                }
                window.dispatchEvent(
                  new CustomEvent("activate-create-image-mode"),
                );
                if (isMobile && onClose) onClose();
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-white/10 text-xs font-medium transition-colors cursor-pointer group"
            >
              <Sparkles
                size={15}
                className="text-gray-400 group-hover:text-blue-400 transition-colors shrink-0"
              />
              <span>Create image</span>
            </button>

            {/* 2. Search (Opens Command Palette / Search Modal) */}
            <button
              type="button"
              onClick={() => {
                if (onOpenSearch) onOpenSearch();
                else window.dispatchEvent(new CustomEvent("open-search"));
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-white/10 text-xs font-medium transition-colors cursor-pointer group"
            >
              <Search
                size={15}
                className="text-gray-400 group-hover:text-white transition-colors shrink-0"
              />
              <span>Search</span>
            </button>

            {/* 3. Connectors (Opens Connectors Screen) */}
            <button
              type="button"
              onClick={() => {
                setIsConnectorsOpen(true);
                window.dispatchEvent(new CustomEvent("open-connectors"));
              }}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-gray-300 hover:text-white hover:bg-white/10 text-xs font-medium transition-colors cursor-pointer group"
            >
              {/* Nodes icon matching screenshot */}
              <svg
                className="w-[15px] h-[15px] text-gray-400 group-hover:text-white transition-colors shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="6" cy="6" r="2.5" />
                <circle cx="6" cy="18" r="2.5" />
                <circle cx="18" cy="12" r="2.5" />
                <path d="M8.5 6h4a4 4 0 0 1 4 4v2" />
                <path d="M8.5 18h4a4 4 0 0 0 4-4v-2" />
              </svg>
              <span>Connectors</span>
            </button>

            {/* 4. Chats (Opens dedicated Chats view from Image 2) */}
            <button
              type="button"
              onClick={() => {
                if (onSelectView) onSelectView("chats");
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-colors cursor-pointer group ${
                currentView === "chats"
                  ? "bg-white/10 text-white"
                  : "text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              <MessageSquare
                size={15}
                className={`shrink-0 transition-colors ${currentView === "chats" ? "text-white" : "text-gray-400 group-hover:text-white"}`}
              />
              <span>Chats</span>
            </button>

            {/* 5. Projects (Opens dedicated Projects view from Image 3) */}
            <button
              type="button"
              onClick={() => {
                if (onSelectView) onSelectView("projects");
              }}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors cursor-pointer group ${
                currentView === "projects"
                  ? "bg-white/10 text-white"
                  : "text-gray-300 hover:text-white hover:bg-white/10"
              }`}
            >
              <div className="flex items-center gap-3">
                <LayoutGrid
                  size={15}
                  className={`shrink-0 transition-colors ${currentView === "projects" ? "text-white" : "text-gray-400 group-hover:text-white"}`}
                />
                <span>Projects</span>
              </div>
              <div className="flex items-center gap-1.5">
                {totalProjectsCount > 0 && (
                  <span className="text-[10px] bg-white/10 text-gray-300 px-1.5 py-0.2 rounded-full font-mono">
                    {totalProjectsCount}
                  </span>
                )}
                <ChevronRight
                  size={13}
                  className="text-gray-400 group-hover:text-white transition-colors"
                />
              </div>
            </button>
          </div>

          {/* Recents Section Header */}
          <div className="flex items-center justify-between px-2 py-1 mb-1 text-gray-400">
            <button
              type="button"
              className="flex items-center gap-1 text-[13px] font-medium text-gray-300 hover:text-white transition-colors cursor-pointer"
            >
              <span>Recents</span>
              <ChevronDown size={13} className="text-gray-400" />
            </button>
            <button
              type="button"
              onClick={() => {
                if (onOpenSearch) onOpenSearch();
                else window.dispatchEvent(new CustomEvent("open-search"));
              }}
              className="p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
              title="Search recents"
            >
              <ListFilter size={14} />
            </button>
          </div>

          {/* Scrollable Recents Chat List */}
          <div
            className="flex-1 overflow-y-auto pr-1 space-y-0.5 scrollbar-thin scrollbar-thumb-white/10"
            onClick={() => setActiveMenuId(null)}
          >
            {isLoading ? (
              <div className="space-y-1.5 py-2 px-1">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-8 bg-white/5 rounded-lg animate-pulse"
                  />
                ))}
              </div>
            ) : (
              conversations.map((conv, idx) => {
                const isActive =
                  activeConversationId === conv.id && currentView === "chat";
                const isRenaming = renamingConvId === conv.id;

                return (
                  <div key={conv.id} className="relative group">
                    {isRenaming ? (
                      <div className="flex items-center gap-1.5 px-2 py-1 bg-white/10 rounded-lg border border-white/20">
                        <input
                          type="text"
                          value={renameTitle}
                          onChange={(e) => setRenameTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") handleSaveRename(conv.id, e);
                            if (e.key === "Escape") setRenamingConvId(null);
                          }}
                          className="flex-1 bg-transparent text-xs text-white outline-none"
                          autoFocus
                          onClick={(e) => e.stopPropagation()}
                        />
                        <button
                          type="button"
                          onClick={(e) => handleSaveRename(conv.id, e)}
                          className="p-1 text-emerald-400 hover:text-emerald-300"
                        >
                          <Check size={13} />
                        </button>
                        <button
                          type="button"
                          onClick={() => setRenamingConvId(null)}
                          className="p-1 text-gray-400 hover:text-white"
                        >
                          <X size={13} />
                        </button>
                      </div>
                    ) : (
                      <div
                        onClick={() => {
                          if (onSelectView) onSelectView("chat");
                          onSelectConversation(conv.id);
                        }}
                        className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs transition-colors cursor-pointer ${
                          isActive
                            ? "bg-white/10 text-white font-medium"
                            : "text-gray-300 hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        <div className="flex items-center gap-2.5 truncate min-w-0 pr-2">
                          {conv.is_pinned ? (
                            <Pin
                              size={13}
                              className="text-amber-400 shrink-0"
                            />
                          ) : idx === 1 ? (
                            <Diamond
                              size={13}
                              className="text-gray-400 group-hover:text-white transition-colors shrink-0"
                            />
                          ) : (
                            <MessageSquare
                              size={14}
                              className="text-gray-400 group-hover:text-white transition-colors shrink-0"
                            />
                          )}
                          <span className="truncate">
                            {conv.title || "New chat"}
                          </span>
                        </div>

                        <div className="flex items-center gap-1 shrink-0">
                          {/* Active Blue Dot from screenshot */}
                          {isActive && (
                            <span
                              className="w-1.5 h-1.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.9)] shrink-0"
                              title="Active chat"
                            />
                          )}

                          {/* Context menu trigger */}
                          <button
                            type="button"
                            onClick={(e) => handleMenuClick(e, conv.id)}
                            className={`p-1 rounded-md text-gray-400 hover:text-white hover:bg-white/10 transition-opacity ${
                              activeMenuId === conv.id
                                ? "opacity-100"
                                : "opacity-0 group-hover:opacity-100"
                            }`}
                            title="More options"
                          >
                            <MoreHorizontal size={14} />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Context Menu Dropdown */}
                    <AnimatePresence>
                      {activeMenuId === conv.id && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.95, y: -5 }}
                          animate={{ opacity: 1, scale: 1, y: 0 }}
                          exit={{ opacity: 0, scale: 0.95, y: -5 }}
                          transition={{ duration: 0.15 }}
                          className="absolute right-2 top-full mt-1 w-44 bg-[#1a1922] border border-white/10 rounded-xl shadow-2xl z-50 py-1.5 backdrop-blur-xl text-gray-200"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <button
                            type="button"
                            onClick={(e) =>
                              handleTogglePinConversation(
                                conv.id,
                                conv.is_pinned,
                                e,
                              )
                            }
                            className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                          >
                            <Pin size={13} className="text-gray-400" />
                            <span>
                              {conv.is_pinned ? "Unpin chat" : "Pin chat"}
                            </span>
                          </button>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveMenuId(null);
                              setRenamingConvId(conv.id);
                              setRenameTitle(conv.title || "");
                            }}
                            className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
                          >
                            <Edit2 size={13} className="text-gray-400" />
                            <span>Rename</span>
                          </button>

                          <div className="h-px bg-white/10 my-1 mx-2" />

                          <button
                            type="button"
                            onClick={(e) =>
                              handleDeleteConversation(conv.id, e)
                            }
                            className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors"
                          >
                            <Trash2 size={13} />
                            <span>Delete</span>
                          </button>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })
            )}
          </div>

          {/* Bottom Upgrade to Pro Card */}
          <div className="pt-2">
            <div className="relative rounded-2xl bg-[#16151d] border border-white/10 p-3 flex items-center justify-between overflow-hidden shadow-lg group">
              <div className="flex flex-col min-w-0 pr-2">
                <span className="text-sm font-semibold text-white tracking-tight">
                  Upgrade to Pro
                </span>
                <span className="text-xs text-gray-400 mt-0.5">
                  Unlock more features
                </span>
              </div>

              <button
                type="button"
                className="w-9 h-9 rounded-full bg-[#5b3bf5] hover:bg-[#6c4ef7] flex items-center justify-center text-white shadow-lg shadow-purple-900/50 transition-all cursor-pointer shrink-0"
                title="Upgrade to Pro"
              >
                <Zap size={16} className="fill-white text-white" />
              </button>

              {/* Subtle bottom purple rim light from screenshot */}
              <div className="absolute -bottom-[1px] left-5 right-5 h-[2px] bg-gradient-to-r from-transparent via-purple-500/80 to-pink-500/80 blur-[0.8px]" />
            </div>
          </div>

          {/* Bottom User Profile Row */}
          <div className="pt-2">
            <div className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-white/10 transition-colors group">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="relative">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-semibold text-xs shrink-0 shadow-sm">
                    {userInitial}
                  </div>
                  {/* Status dot */}
                  <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-[#0c0b10]" />
                </div>

                <div className="flex flex-col min-w-0">
                  <span className="text-xs font-semibold text-white truncate max-w-[130px]">
                    {userName}
                  </span>
                  <span className="text-[10px] text-gray-400 truncate">
                    {userEmail || "Signed in"}
                  </span>
                </div>
              </div>

              {/* Logout button */}
              <button
                type="button"
                onClick={() => logout()}
                className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-red-800 dark:hover:bg-red-800/90 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-red-950/40"
                title="Log out"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Connectors Full Modal */}
      <ConnectorsModal
        isOpen={isConnectorsOpen}
        onClose={() => setIsConnectorsOpen(false)}
      />
    </>
  );
}
