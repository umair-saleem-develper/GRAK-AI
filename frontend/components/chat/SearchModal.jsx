"use client";
import React, { useState, useEffect } from "react";
import Image from "next/image";
import {
  Search,
  MessageSquare,
  LayoutGrid,
  Home,
  Plus,
  CornerDownLeft,
  Diamond,
  Sparkles,
  X,
  Folder,
  Clock,
} from "lucide-react";

export default function SearchModal({
  isOpen,
  onClose,
  conversations = [],
  projects = [],
  folders = [],
  onSelectConversation,
  onNavigateView,
  onCreateProject,
  onSelectProject,
  userName = "Main Umair",
}) {
  const [open, setOpen] = useState(isOpen || false);
  const [query, setQuery] = useState("");
  const [selectedItem, setSelectedItem] = useState(null);

  useEffect(() => {
    if (typeof isOpen === "boolean") setOpen(isOpen);
  }, [isOpen]);

  // Global event & Ctrl+K shortcut listener
  useEffect(() => {
    const handleOpen = () => setOpen(true);
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
      if (e.key === "Escape" && open) {
        setOpen(false);
        if (onClose) onClose();
      }
    };

    window.addEventListener("open-search", handleOpen);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("open-search", handleOpen);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, onClose]);

  const handleClose = () => {
    setOpen(false);
    if (onClose) onClose();
  };

  const handleOpenAction = () => {
    if (!selectedItem) return;
    if (selectedItem.type === "project") {
      const proj = projects.find((p) => p.id === selectedItem.id);
      if (proj && onSelectProject) {
        onSelectProject(proj);
      } else if (onNavigateView) {
        onNavigateView("projects");
      }
    } else if (selectedItem.type === "folder") {
      if (onNavigateView) onNavigateView("projects");
    } else if (selectedItem.type === "chat") {
      if (onSelectConversation) onSelectConversation(selectedItem.id);
      if (onNavigateView) onNavigateView("chat");
    } else if (selectedItem.type === "nav") {
      if (selectedItem.id === "dashboard") onNavigateView("chat");
      else if (selectedItem.id === "chats") onNavigateView("chats");
      else if (selectedItem.id === "new-project") {
        if (onCreateProject) onCreateProject();
        onNavigateView("projects");
      }
    }
    handleClose();
  };

  // Filtered lists (No hardcoded dummy projects)
  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(query.toLowerCase()),
  );
  const filteredFolders = folders.filter((f) =>
    f.name.toLowerCase().includes(query.toLowerCase()),
  );
  const filteredChats = conversations.filter((c) =>
    (c.title || "New chat").toLowerCase().includes(query.toLowerCase()),
  );

  // Auto-select first item if current selectedItem is null or not found
  useEffect(() => {
    if (!selectedItem) {
      if (filteredFolders.length > 0) {
        const f = filteredFolders[0];
        setSelectedItem({
          type: "folder",
          id: f.id,
          title: f.name,
          owner: userName || "Main Umair",
          status: f.visibility === "personal" ? "Personal" : "Workspace",
          created: f.createdAt
            ? new Date(f.createdAt).toLocaleDateString()
            : "Recent",
          lastEdited: "Recently",
          lastOpened: "Recently",
          description: `Folder "${f.name}" grouped in your workspace.`,
        });
      } else if (filteredProjects.length > 0) {
        const p = filteredProjects[0];
        setSelectedItem({
          type: "project",
          id: p.id,
          title: p.name,
          owner: p.owner || userName || "Main Umair",
          status: "Workspace",
          created: p.createdAt
            ? new Date(p.createdAt).toLocaleDateString()
            : "Recent",
          lastEdited: "Recently",
          lastOpened: "Recently",
          description: `${p.name} workspace project.`,
        });
      } else if (filteredChats.length > 0) {
        const c = filteredChats[0];
        setSelectedItem({
          type: "chat",
          id: c.id,
          title: c.title || "New chat",
          owner: userName || "Main Umair",
          status: "Chat",
          created: c.created_at
            ? new Date(c.created_at).toLocaleDateString()
            : "Recent",
          lastEdited: c.updated_at
            ? new Date(c.updated_at).toLocaleDateString()
            : "Recent",
          lastOpened: "Recently",
          description: `Saved chat conversation titled "${c.title || "New chat"}".`,
        });
      }
    }
  }, [
    filteredProjects,
    filteredFolders,
    filteredChats,
    selectedItem,
    userName,
  ]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-150"
      onClick={handleClose}
    >
      <div
        className="w-full max-w-4xl bg-[#14131a] border border-white/10 rounded-2xl shadow-[0_25px_80px_rgba(0,0,0,0.85)] flex flex-col overflow-hidden text-gray-200 animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Search Input */}
        <div className="relative flex items-center px-5 py-4 border-b border-white/5 bg-[#181720]/80">
          <input
            type="text"
            placeholder="Search..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleOpenAction();
            }}
            className="w-full bg-transparent text-lg text-white placeholder-gray-500 outline-none pr-8 font-medium"
            autoFocus
          />
          <button
            type="button"
            onClick={handleClose}
            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Two-Column Body */}
        <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-white/5 min-h-[360px] max-h-[500px] overflow-hidden">
          {/* Left Column: Lists */}
          <div className="overflow-y-auto p-3 space-y-4 scrollbar-thin scrollbar-thumb-white/10">
            {/* Recent projects / Folders (Only if any exist) */}
            {(filteredFolders.length > 0 || filteredProjects.length > 0) && (
              <div>
                <div className="text-[11px] font-semibold text-gray-400 px-2 mb-1.5">
                  Recent projects & folders
                </div>
                <div className="space-y-1">
                  {/* Folders */}
                  {filteredFolders.map((f) => {
                    const isSelected = selectedItem?.id === f.id;
                    return (
                      <div
                        key={f.id}
                        onClick={() =>
                          setSelectedItem({
                            type: "folder",
                            id: f.id,
                            title: f.name,
                            owner: userName || "Main Umair",
                            status:
                              f.visibility === "personal"
                                ? "Personal"
                                : "Workspace",
                            created: f.createdAt
                              ? new Date(f.createdAt).toLocaleDateString()
                              : "Recent",
                            lastEdited: "Recently",
                            lastOpened: "Recently",
                            description: `Folder "${f.name}" grouped in your workspace.`,
                          })
                        }
                        onDoubleClick={handleOpenAction}
                        className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-blue-600 text-white shadow-sm"
                            : "text-gray-300 hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        <Folder
                          size={14}
                          className={
                            isSelected ? "text-white" : "text-gray-400"
                          }
                        />
                        <span className="truncate">{f.name}</span>
                      </div>
                    );
                  })}

                  {/* Projects */}
                  {filteredProjects.map((p) => {
                    const isSelected = selectedItem?.id === p.id;
                    return (
                      <div
                        key={p.id}
                        onClick={() =>
                          setSelectedItem({
                            type: "project",
                            id: p.id,
                            title: p.name,
                            owner: p.owner || userName || "Main Umair",
                            status: "Workspace",
                            created: p.createdAt
                              ? new Date(p.createdAt).toLocaleDateString()
                              : "Recent",
                            lastEdited: "Recently",
                            lastOpened: "Recently",
                            description: `${p.name} workspace project.`,
                          })
                        }
                        onDoubleClick={handleOpenAction}
                        className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-blue-600 text-white shadow-sm"
                            : "text-gray-300 hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        <Diamond
                          size={14}
                          className={
                            isSelected ? "text-white" : "text-gray-400"
                          }
                        />
                        <span className="truncate">{p.name}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recent chats */}
            {filteredChats.length > 0 && (
              <div>
                <div className="text-[11px] font-semibold text-gray-400 px-2 mb-1.5">
                  Recent chats
                </div>
                <div className="space-y-1">
                  {filteredChats.slice(0, 6).map((c) => {
                    const isSelected = selectedItem?.id === c.id;
                    return (
                      <div
                        key={c.id}
                        onClick={() =>
                          setSelectedItem({
                            type: "chat",
                            id: c.id,
                            title: c.title || "New chat",
                            owner: userName || "Main Umair",
                            status: "Chat",
                            created: c.created_at
                              ? new Date(c.created_at).toLocaleDateString()
                              : "Recent",
                            lastEdited: c.updated_at
                              ? new Date(c.updated_at).toLocaleDateString()
                              : "Recent",
                            lastOpened: "Just now",
                            description: `Saved chat conversation titled "${c.title || "New chat"}" in your workspace.`,
                          })
                        }
                        onDoubleClick={handleOpenAction}
                        className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                          isSelected
                            ? "bg-blue-600 text-white shadow-sm"
                            : "text-gray-300 hover:bg-white/10 hover:text-white"
                        }`}
                      >
                        <MessageSquare
                          size={14}
                          className={
                            isSelected ? "text-white" : "text-gray-400"
                          }
                        />
                        <span className="truncate">
                          {c.title || "New chat"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Navigate to */}
            <div>
              <div className="text-[11px] font-semibold text-gray-400 px-2 mb-1.5">
                Navigate to
              </div>
              <div className="space-y-1">
                <div
                  onClick={() => {
                    if (onNavigateView) onNavigateView("chat");
                    handleClose();
                  }}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-gray-300 hover:bg-white/10 hover:text-white cursor-pointer transition-colors"
                >
                  <Home size={14} className="text-gray-400" />
                  <span>Dashboard</span>
                </div>

                <div
                  onClick={() => {
                    if (onCreateProject) onCreateProject();
                    if (onNavigateView) onNavigateView("projects");
                    handleClose();
                  }}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-gray-300 hover:bg-white/10 hover:text-white cursor-pointer transition-colors"
                >
                  <Plus size={14} className="text-gray-400" />
                  <span>Create new project</span>
                </div>

                <div
                  onClick={() => {
                    if (onNavigateView) onNavigateView("chats");
                    handleClose();
                  }}
                  className="flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium text-gray-300 hover:bg-white/10 hover:text-white cursor-pointer transition-colors"
                >
                  <MessageSquare size={14} className="text-gray-400" />
                  <span>Chats</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Details & Preview Pane */}
          <div className="p-5 flex flex-col justify-between bg-[#111017]/70 overflow-y-auto">
            {selectedItem ? (
              <div className="space-y-4">
                {/* Futuristic Project / Chat Thumbnail Preview */}
                <div className="relative w-full h-44 rounded-xl overflow-hidden border border-white/10 bg-[#09090e] flex flex-col shadow-inner">
                  <div className="flex-1 p-3 flex flex-col justify-between relative bg-gradient-to-br from-[#051824]/90 via-[#070e17] to-[#040810]">
                    {/* Top bar of preview */}
                    <div className="flex items-center justify-between text-[8px] text-cyan-400 font-mono tracking-widest uppercase">
                      <span>• {selectedItem.title.toUpperCase()}</span>
                      <span className="text-cyan-500/70">
                        {selectedItem.status.toUpperCase()}
                      </span>
                    </div>

                    {/* Middle: Radar orb and telemetry cards */}
                    <div className="grid grid-cols-3 gap-2 my-auto items-center">
                      <div className="p-1.5 rounded bg-cyan-950/30 border border-cyan-800/30 text-[7px] text-cyan-300 space-y-0.5">
                        <div className="font-bold">STATUS</div>
                        <div className="text-[6px] text-cyan-400/70">
                          Online & Ready
                        </div>
                      </div>

                      {/* Glowing center circle */}
                      <div className="w-14 h-14 mx-auto rounded-full border border-cyan-500/40 p-1 flex items-center justify-center relative shadow-[0_0_15px_rgba(6,182,212,0.3)]">
                        <div className="w-full h-full rounded-full bg-gradient-to-tr from-cyan-600 via-teal-400 to-emerald-400 animate-pulse flex items-center justify-center text-[7px] font-bold text-black">
                          {selectedItem.type.toUpperCase()}
                        </div>
                      </div>

                      <div className="p-1.5 rounded bg-cyan-950/30 border border-cyan-800/30 text-[7px] text-cyan-300 space-y-0.5">
                        <div className="font-bold">WORKSPACE</div>
                        <div className="text-[6px] text-cyan-400/70">
                          Active Node
                        </div>
                      </div>
                    </div>

                    {/* Bottom grid line */}
                    <div className="h-[1px] w-full bg-gradient-to-r from-transparent via-cyan-500/40 to-transparent" />
                  </div>
                </div>

                {/* Title */}
                <div>
                  <h3 className="text-lg font-bold text-white tracking-tight">
                    {selectedItem.title}
                  </h3>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 gap-y-3 text-xs">
                  <div>
                    <span className="text-[11px] text-gray-500 block">
                      Owner
                    </span>
                    <span className="font-medium text-gray-200">
                      {selectedItem.owner}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-gray-500 block">
                      Status
                    </span>
                    <span className="font-medium text-gray-200">
                      {selectedItem.status}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-gray-500 block">
                      Created
                    </span>
                    <span className="text-gray-300">
                      {selectedItem.created}
                    </span>
                  </div>
                  <div>
                    <span className="text-[11px] text-gray-500 block">
                      Last edited
                    </span>
                    <span className="text-gray-300">
                      {selectedItem.lastEdited}
                    </span>
                  </div>
                </div>

                {/* Description */}
                <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">
                  {selectedItem.description}
                </p>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-xs text-gray-500 space-y-2">
                <Search size={24} className="opacity-30" />
                <span>Select an item or search above</span>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="px-5 py-3 border-t border-white/5 bg-[#14131a] flex items-center justify-between text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-white/10 flex items-center justify-center">
              <Sparkles size={11} className="text-white" />
            </div>
            <span className="text-[11px]">Navigate with ↑↓ and Enter</span>
          </div>

          <button
            type="button"
            onClick={handleOpenAction}
            disabled={!selectedItem}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-40 text-white font-medium transition-colors cursor-pointer"
          >
            <span>Open {selectedItem?.type || "item"}</span>
            <CornerDownLeft size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
