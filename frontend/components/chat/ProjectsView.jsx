"use client";
import React, { useState } from "react";
import {
  Search,
  ChevronDown,
  Plus,
  FolderPlus,
  MoreHorizontal,
  Trash2,
  X,
  Folder,
  LayoutGrid,
  Zap,
  PenSquare,
  ArrowRightLeft,
  Check,
  Grid,
  List,
  ChevronRight,
} from "lucide-react";

export default function ProjectsView({
  projects = [],
  folders = [],
  onCreateProject,
  onDeleteProject,
  onSelectProject,
  onUpdateProject,
  onCreateFolder,
  onDeleteFolder,
  onUpdateFolder,
  userName = "Main Umair",
  userInitial = "M",
}) {
  const [search, setSearch] = useState("");

  // Navigation: currentFolderId (null = root Projects view, string = inside that folder)
  const [currentFolderId, setCurrentFolderId] = useState(null);

  // Modals state
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false);
  const [isSubfolderModalOpen, setIsSubfolderModalOpen] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isAddExistingProjectModalOpen, setIsAddExistingProjectModalOpen] =
    useState(false);

  // Folder Creation State
  const [newFolderName, setNewFolderName] = useState("");

  // Project Creation State
  const [newProjectName, setNewProjectName] = useState("");

  // Context Menu & Editing State
  const [activeFolderMenuId, setActiveFolderMenuId] = useState(null);
  const [editingFolderId, setEditingFolderId] = useState(null);
  const [editingFolderName, setEditingFolderName] = useState("");
  const [isCurrentFolderMenuOpen, setIsCurrentFolderMenuOpen] = useState(false);

  // Toolbar Dropdown States
  const [filterType, setFilterType] = useState("All"); // "All" | "Last viewed" | "Created" | "Alphabetical"
  const [isFilterDropdownOpen, setIsFilterDropdownOpen] = useState(false);
  const [viewMode, setViewMode] = useState("grid"); // "grid" | "list"
  const [isViewDropdownOpen, setIsViewDropdownOpen] = useState(false);

  // Current folder object (if inside a folder)
  const currentFolder = currentFolderId
    ? folders.find((f) => f.id === currentFolderId)
    : null;

  // Items for Root View vs. Folder View
  const displayedFolders =
    currentFolderId === null
      ? folders.filter((f) => !f.parentId) // Root folders
      : folders.filter((f) => f.parentId === currentFolderId); // Subfolders of current folder

  const displayedProjects =
    currentFolderId === null
      ? projects.filter((p) => !p.folderId) // Root projects
      : projects.filter((p) => p.folderId === currentFolderId); // Projects inside current folder

  // Filter with Search
  let filteredFolders = displayedFolders.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase()),
  );
  let filteredProjects = displayedProjects.filter((p) =>
    p.name.toLowerCase().includes(search.toLowerCase()),
  );

  // Apply sorting based on filterType
  if (filterType === "Alphabetical") {
    filteredFolders = [...filteredFolders].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
    filteredProjects = [...filteredProjects].sort((a, b) =>
      a.name.localeCompare(b.name),
    );
  } else if (filterType === "Created") {
    filteredFolders = [...filteredFolders].sort(
      (a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0),
    );
    filteredProjects = [...filteredProjects].sort(
      (a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0),
    );
  }

  // Handle Root Folder Submit
  const handleCreateFolder = (e) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    if (onCreateFolder) {
      onCreateFolder({
        name: newFolderName.trim(),
        visibility: "workspace",
        parentId: null,
      });
    }
    setNewFolderName("");
    setIsFolderModalOpen(false);
  };

  // Handle Subfolder Submit
  const handleCreateSubfolder = (e) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;
    if (onCreateFolder) {
      onCreateFolder({
        name: newFolderName.trim(),
        visibility: "workspace",
        parentId: currentFolderId,
      });
    }
    setNewFolderName("");
    setIsSubfolderModalOpen(false);
  };

  // Handle Project Submit (creates project and immediately switches to new chat)
  const handleCreateProject = (e) => {
    e.preventDefault();
    const projName =
      newProjectName.trim() ||
      (currentFolder ? `${currentFolder.name} Project` : "New Project");
    if (onCreateProject) {
      onCreateProject(projName, currentFolderId);
    }
    setNewProjectName("");
    setIsProjectModalOpen(false);
  };

  // Handle Save Rename Folder
  const handleSaveRenameFolder = (folderId) => {
    if (!editingFolderName.trim()) {
      setEditingFolderId(null);
      return;
    }
    if (onUpdateFolder) {
      onUpdateFolder(folderId, { name: editingFolderName.trim() });
    }
    setEditingFolderId(null);
    setEditingFolderName("");
  };

  // Handle adding an existing project into current folder
  const handleAddProjectToCurrentFolder = (projId) => {
    if (onUpdateProject) {
      onUpdateProject(projId, { folderId: currentFolderId });
    }
    setIsAddExistingProjectModalOpen(false);
  };

  // Projects that can be added into the current folder (i.e. not yet in this folder)
  const candidateProjectsToAdd = projects.filter(
    (p) => p.folderId !== currentFolderId,
  );

  // Check if current folder is completely empty
  const isFolderEmpty =
    currentFolderId !== null &&
    displayedFolders.length === 0 &&
    displayedProjects.length === 0;

  return (
    <div
      className="flex-1 h-full overflow-y-auto px-6 py-8 md:px-12 md:py-10 text-gray-200 bg-[#0c0b10] relative z-10"
      onClick={() => {
        setActiveFolderMenuId(null);
        setIsFilterDropdownOpen(false);
        setIsViewDropdownOpen(false);
        setIsCurrentFolderMenuOpen(false);
      }}
    >
      <div className="max-w-5xl mx-auto space-y-6">
        {/* ======================================================== */}
        {/* Top Header / Breadcrumb                                  */}
        {/* ======================================================== */}
        <div className="flex items-center justify-between pb-2">
          {currentFolderId === null ? (
            /* Root Projects Header */
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Projects
            </h1>
          ) : (
            /* Inside Folder Breadcrumb matching media_1792307469395_b76962a6.png */
            <div className="flex items-center gap-2 relative">
              <button
                type="button"
                onClick={() => setCurrentFolderId(null)}
                className="text-gray-400 hover:text-white transition-colors text-base sm:text-lg font-medium cursor-pointer"
              >
                Projects
              </button>
              <ChevronRight size={16} className="text-gray-500" />
              <span className="text-white font-bold text-lg sm:text-xl tracking-tight">
                {currentFolder?.name || "Folder"}
              </span>

              {/* Three dots menu for current folder */}
              <div className="relative">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsCurrentFolderMenuOpen(!isCurrentFolderMenuOpen);
                  }}
                  className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors ml-1 cursor-pointer"
                  title="Folder options"
                >
                  <MoreHorizontal size={17} />
                </button>

                {isCurrentFolderMenuOpen && (
                  <div
                    className="absolute left-0 top-full mt-1.5 w-44 bg-[#23222a] border border-white/10 rounded-2xl shadow-2xl z-40 py-2 backdrop-blur-xl text-gray-200 animate-in fade-in zoom-in-95 duration-100"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        setIsCurrentFolderMenuOpen(false);
                        setEditingFolderId(currentFolder.id);
                        setEditingFolderName(currentFolder.name);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-xs font-medium text-gray-200 hover:text-white hover:bg-white/10 transition-colors"
                    >
                      <PenSquare size={14} className="text-gray-400" />
                      <span>Edit folder</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setIsCurrentFolderMenuOpen(false);
                        if (onDeleteFolder) onDeleteFolder(currentFolder.id);
                        setCurrentFolderId(null);
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                    >
                      <Trash2 size={14} className="text-red-400" />
                      <span>Delete folder</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Top Right Action Buttons */}
          <div className="flex items-center gap-2.5">
            {currentFolderId === null ? (
              <>
                {/* New folder button */}
                <button
                  type="button"
                  onClick={() => setIsFolderModalOpen(true)}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium text-gray-300 hover:text-white bg-white/10 hover:bg-white/15 border border-white/10 transition-colors cursor-pointer"
                >
                  <FolderPlus size={13} />
                  <span>New folder</span>
                </button>

                {/* New project button */}
                <button
                  type="button"
                  onClick={() => setIsProjectModalOpen(true)}
                  className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-full text-xs font-semibold shadow-md shadow-blue-900/30 transition-all cursor-pointer active:scale-95"
                >
                  <span>New project</span>
                </button>
              </>
            ) : (
              /* Inside Folder Top Right Buttons matching media_1792307469395_b76962a6.png */
              <>
                <button
                  type="button"
                  onClick={() => setIsSubfolderModalOpen(true)}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-medium text-gray-300 hover:text-white bg-white/10 hover:bg-white/15 border border-white/10 transition-colors cursor-pointer"
                >
                  <span>New subfolder</span>
                </button>

                <button
                  type="button"
                  onClick={() => setIsProjectModalOpen(true)}
                  className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-full text-xs font-semibold shadow-md shadow-blue-900/30 transition-all cursor-pointer active:scale-95"
                >
                  <span>New project</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* ======================================================== */}
        {/* Empty Folder State (Exact match to uploaded image)       */}
        {/* ======================================================== */}
        {isFolderEmpty ? (
          <div className="flex flex-col items-center justify-center min-h-[380px] my-auto text-center space-y-4 pt-16 pb-12">
            <div className="w-14 h-14 rounded-2xl flex items-center justify-center text-gray-400 bg-white/[0.02]">
              <Folder size={42} strokeWidth={1.4} />
            </div>

            <div className="space-y-1.5">
              <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">
                This folder is empty
              </h3>
              <p className="text-xs text-gray-400 max-w-sm mx-auto leading-relaxed">
                Create new projects, add existing ones, or create subfolders to
                organize your work.
              </p>
            </div>

            <div className="flex items-center gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setIsSubfolderModalOpen(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium text-white border border-white/15 bg-transparent hover:bg-white/10 transition-colors cursor-pointer"
              >
                <FolderPlus size={14} className="text-gray-300" />
                <span>New subfolder</span>
              </button>

              <button
                type="button"
                onClick={() => setIsAddExistingProjectModalOpen(true)}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-medium text-white border border-white/15 bg-white/10 hover:bg-white/15 transition-colors cursor-pointer"
              >
                <Plus size={14} className="text-gray-300" />
                <span>Add existing project</span>
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Toolbar: Search, Filter, View */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
              <div className="relative flex-1">
                <Search
                  size={14}
                  className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  type="text"
                  placeholder={
                    currentFolderId
                      ? `Search in ${currentFolder?.name || "folder"}...`
                      : "Search projects..."
                  }
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full bg-[#181720]/80 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 outline-none focus:border-white/20 transition-colors"
                />
              </div>

              <div className="flex items-center gap-2 relative">
                {/* Filter Dropdown */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsFilterDropdownOpen(!isFilterDropdownOpen);
                      setIsViewDropdownOpen(false);
                    }}
                    className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#181720]/80 border border-white/10 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                  >
                    <span>{filterType === "All" ? "Filter" : filterType}</span>
                    <ChevronDown size={13} className="text-gray-400" />
                  </button>

                  {isFilterDropdownOpen && (
                    <div
                      className="absolute right-0 top-full mt-1.5 w-36 bg-[#1b1a23] border border-white/10 rounded-xl shadow-xl z-30 py-1 text-xs"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {["All", "Last viewed", "Created", "Alphabetical"].map(
                        (opt) => (
                          <button
                            key={opt}
                            type="button"
                            onClick={() => {
                              setFilterType(opt);
                              setIsFilterDropdownOpen(false);
                            }}
                            className={`w-full text-left px-3 py-1.5 text-xs hover:bg-white/10 hover:text-white transition-colors flex items-center justify-between ${
                              filterType === opt
                                ? "text-blue-400 font-semibold"
                                : "text-gray-300"
                            }`}
                          >
                            <span>{opt}</span>
                            {filterType === opt && <Check size={12} />}
                          </button>
                        ),
                      )}
                    </div>
                  )}
                </div>

                {/* View Mode Toggle Dropdown */}
                <div className="relative">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsViewDropdownOpen(!isViewDropdownOpen);
                      setIsFilterDropdownOpen(false);
                    }}
                    className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#181720]/80 border border-white/10 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                  >
                    {viewMode === "grid" ? (
                      <Grid size={13} />
                    ) : (
                      <List size={13} />
                    )}
                    <span className="capitalize">{viewMode}</span>
                    <ChevronDown size={13} className="text-gray-400" />
                  </button>

                  {isViewDropdownOpen && (
                    <div
                      className="absolute right-0 top-full mt-1.5 w-32 bg-[#1b1a23] border border-white/10 rounded-xl shadow-xl z-30 py-1 text-xs"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setViewMode("grid");
                          setIsViewDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-1.5 text-xs hover:bg-white/10 hover:text-white transition-colors flex items-center justify-between ${
                          viewMode === "grid"
                            ? "text-blue-400 font-semibold"
                            : "text-gray-300"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <Grid size={12} /> Grid
                        </span>
                        {viewMode === "grid" && <Check size={12} />}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setViewMode("list");
                          setIsViewDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-1.5 text-xs hover:bg-white/10 hover:text-white transition-colors flex items-center justify-between ${
                          viewMode === "list"
                            ? "text-blue-400 font-semibold"
                            : "text-gray-300"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <List size={12} /> List
                        </span>
                        {viewMode === "list" && <Check size={12} />}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Folders / Subfolders Section (Pill style matching Image 3) */}
            {filteredFolders.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {filteredFolders.map((folder) => {
                    const isMenuOpen = activeFolderMenuId === folder.id;
                    const isEditing = editingFolderId === folder.id;

                    return (
                      <div key={folder.id} className="relative">
                        <div
                          className="group flex items-center justify-between px-4 py-3 rounded-2xl bg-[#222129] border border-white/5 hover:border-white/15 transition-all shadow-md hover:shadow-lg cursor-pointer"
                          onClick={() => {
                            // Clicking folder navigates into it!
                            setCurrentFolderId(folder.id);
                          }}
                        >
                          <div className="flex items-center gap-3 min-w-0 flex-1">
                            <Folder
                              size={18}
                              className="text-gray-300 shrink-0"
                            />
                            {isEditing ? (
                              <div
                                className="flex items-center gap-1 flex-1"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <input
                                  type="text"
                                  value={editingFolderName}
                                  onChange={(e) =>
                                    setEditingFolderName(e.target.value)
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter")
                                      handleSaveRenameFolder(folder.id);
                                    if (e.key === "Escape")
                                      setEditingFolderId(null);
                                  }}
                                  className="w-full bg-white/10 text-xs text-white px-2 py-0.5 rounded border border-white/20 outline-none"
                                  autoFocus
                                />
                                <button
                                  type="button"
                                  onClick={() =>
                                    handleSaveRenameFolder(folder.id)
                                  }
                                  className="p-1 text-emerald-400 hover:text-emerald-300"
                                >
                                  <Check size={13} />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setEditingFolderId(null)}
                                  className="p-1 text-gray-400 hover:text-white"
                                >
                                  <X size={13} />
                                </button>
                              </div>
                            ) : (
                              <span className="font-semibold text-sm text-white truncate">
                                {folder.name}
                              </span>
                            )}
                          </div>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveFolderMenuId(
                                isMenuOpen ? null : folder.id,
                              );
                            }}
                            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors ml-2"
                            title="More options"
                          >
                            <MoreHorizontal size={16} />
                          </button>
                        </div>

                        {/* Folder Context Menu Dropdown */}
                        {isMenuOpen && (
                          <div
                            className="absolute left-4 top-full mt-1.5 w-48 bg-[#23222a] border border-white/10 rounded-2xl shadow-2xl z-40 py-2 backdrop-blur-xl text-gray-200 animate-in fade-in zoom-in-95 duration-100"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <button
                              type="button"
                              onClick={() => {
                                setActiveFolderMenuId(null);
                                setCurrentFolderId(folder.id);
                                setIsProjectModalOpen(true);
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2 text-xs font-medium text-gray-200 hover:text-white hover:bg-white/10 transition-colors"
                            >
                              <Plus size={14} className="text-gray-400" />
                              <span>Add projects</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setActiveFolderMenuId(null);
                                setEditingFolderId(folder.id);
                                setEditingFolderName(folder.name);
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2 text-xs font-medium text-gray-200 hover:text-white hover:bg-white/10 transition-colors"
                            >
                              <PenSquare size={14} className="text-gray-400" />
                              <span>Edit</span>
                            </button>

                            <button
                              type="button"
                              onClick={() => {
                                setActiveFolderMenuId(null);
                                if (onDeleteFolder) onDeleteFolder(folder.id);
                                if (currentFolderId === folder.id)
                                  setCurrentFolderId(null);
                              }}
                              className="w-full flex items-center gap-3 px-4 py-2 text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                            >
                              <Trash2 size={14} className="text-red-400" />
                              <span>Delete</span>
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Projects Cards Grid / List (Only real user-created projects with Glowing Green Orb) */}
            {filteredProjects.length > 0 && (
              <div
                className={
                  viewMode === "grid"
                    ? "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 pt-3"
                    : "space-y-3 pt-3"
                }
              >
                {filteredProjects.map((proj) => {
                  if (viewMode === "list") {
                    return (
                      <div
                        key={proj.id}
                        onClick={() => {
                          if (onSelectProject) onSelectProject(proj);
                        }}
                        className="flex items-center justify-between p-3.5 rounded-xl bg-[#14131a] border border-white/5 hover:border-white/15 transition-all shadow-sm group cursor-pointer hover:bg-white/[0.02]"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-8 h-8 rounded-full bg-[#8c6b54] text-white font-semibold text-xs flex items-center justify-center shrink-0 shadow-sm">
                            {userInitial}
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="font-semibold text-sm text-white group-hover:text-emerald-400 transition-colors truncate">
                              {proj.name}
                            </span>
                            <span className="text-[11px] text-gray-400 truncate">
                              {proj.conversationId
                                ? "Linked to chat • Click to open"
                                : proj.createdAt
                                  ? `Created ${new Date(proj.createdAt).toLocaleDateString()}`
                                  : "Click to start chat"}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onDeleteProject) onDeleteProject(proj.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 p-1.5 rounded-lg hover:bg-white/10 transition-all"
                          title="Delete project"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={proj.id}
                      onClick={() => {
                        if (onSelectProject) onSelectProject(proj);
                      }}
                      className="group flex flex-col rounded-2xl bg-[#14131a] border border-white/5 hover:border-emerald-500/30 overflow-hidden transition-all shadow-md hover:shadow-xl cursor-pointer hover:scale-[1.01]"
                    >
                      {/* Futuristic Green Radar Orb Thumbnail matching user's reference */}
                      <div className="relative w-full h-40 bg-[#070b09] border-b border-white/5 overflow-hidden flex flex-col justify-between p-3 group-hover:bg-[#09110d] transition-colors">
                        <div className="flex items-center justify-between text-[8px] text-emerald-400 font-mono tracking-widest uppercase">
                          <span>• {proj.name.toUpperCase()}</span>
                          <span className="text-emerald-500/70">ONLINE</span>
                        </div>

                        {/* Spinning Glowing Green Radar Orb */}
                        <div className="flex items-center justify-center my-auto relative">
                          <div className="relative w-20 h-20 rounded-full border border-emerald-500/40 p-1.5 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.35)] animate-[spin_12s_linear_infinite]">
                            {/* Inner Pulsing Radar Ring */}
                            <div className="w-full h-full rounded-full bg-gradient-to-tr from-emerald-600 via-green-400 to-teal-300 flex items-center justify-center text-[8px] font-bold text-black shadow-inner">
                              CORE
                            </div>
                          </div>
                        </div>

                        <div className="text-[7px] text-emerald-500/80 font-mono text-center truncate">
                          AI WORKSPACE NODE
                        </div>
                      </div>

                      {/* Card Footer Info */}
                      <div className="p-3.5 flex items-center justify-between">
                        <div className="flex items-center gap-3 min-w-0">
                          <div className="w-8 h-8 rounded-full bg-[#8c6b54] text-white font-semibold text-xs flex items-center justify-center shrink-0 shadow-sm">
                            {userInitial}
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="font-semibold text-sm text-white group-hover:text-emerald-400 transition-colors truncate">
                              {proj.name}
                            </span>
                            <span className="text-xs text-gray-400 truncate">
                              {proj.conversationId
                                ? "Linked to chat • Click to open"
                                : proj.createdAt
                                  ? `Created ${new Date(proj.createdAt).toLocaleDateString()}`
                                  : "Click to start chat"}
                            </span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (onDeleteProject) onDeleteProject(proj.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-400 p-1 rounded transition-opacity"
                          title="Delete project"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>

      {/* ======================================================== */}
      {/* 1. Create Folder Modal (Personal option DELETED as requested) */}
      {/* ======================================================== */}
      {(isFolderModalOpen || isSubfolderModalOpen) && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150"
          onClick={() => {
            setIsFolderModalOpen(false);
            setIsSubfolderModalOpen(false);
          }}
        >
          <div
            className="w-full max-w-[460px] bg-[#1e1d24] border border-white/10 rounded-3xl p-6 shadow-2xl text-gray-200 space-y-5 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">
                  {isSubfolderModalOpen ? "Create subfolder" : "Create folder"}
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Group related projects together
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setIsFolderModalOpen(false);
                  setIsSubfolderModalOpen(false);
                }}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form
              onSubmit={
                isSubfolderModalOpen
                  ? handleCreateSubfolder
                  : handleCreateFolder
              }
              className="space-y-5"
            >
              {/* Folder Name Input with Folder Icon */}
              <div className="relative flex items-center rounded-2xl bg-[#16151c] border border-white/10 focus-within:border-blue-500/80 transition-colors px-3.5 py-3">
                <Folder size={18} className="text-gray-400 shrink-0 mr-3" />
                <input
                  type="text"
                  placeholder="e.g. Grak AI"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  className="w-full bg-transparent text-sm text-white placeholder-gray-500 outline-none"
                  autoFocus
                />
              </div>

              {/* Visibility Section: Only Workspace option (Personal option deleted as requested) */}
              <div className="space-y-2.5">
                <label className="text-xs font-bold text-white block">
                  Visibility
                </label>

                {/* Workspace Option with Blue Border */}
                <div className="flex items-start gap-3 p-3.5 rounded-2xl border-2 border-blue-600 bg-blue-600/5 shadow-sm">
                  {/* Radio Indicator */}
                  <div className="pt-0.5">
                    <div className="w-4 h-4 rounded-full flex items-center justify-center border border-blue-500 bg-blue-500">
                      <div className="w-1.5 h-1.5 rounded-full bg-white" />
                    </div>
                  </div>

                  {/* Icon & Details */}
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <LayoutGrid size={15} className="text-gray-300" />
                      <span className="font-bold text-sm text-white">
                        Workspace
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      All workspace members can see and add projects to this
                      folder
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Buttons matching Image 2 */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsFolderModalOpen(false);
                    setIsSubfolderModalOpen(false);
                  }}
                  className="w-full py-2.5 rounded-2xl text-xs font-semibold text-white bg-transparent border border-white/15 hover:bg-white/10 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={!newFolderName.trim()}
                  className={`w-full py-2.5 rounded-2xl text-xs font-semibold transition-all cursor-pointer ${
                    newFolderName.trim()
                      ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30 active:scale-[0.98]"
                      : "bg-[#4a4954] text-gray-300 opacity-60 cursor-not-allowed"
                  }`}
                >
                  Create folder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 2. Create Project Modal                                  */}
      {/* ======================================================== */}
      {isProjectModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150"
          onClick={() => setIsProjectModalOpen(false)}
        >
          <div
            className="w-full max-w-md bg-[#1e1d24] border border-white/10 rounded-3xl p-6 shadow-2xl text-gray-200 space-y-4 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white tracking-tight">
                  Create project
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  {currentFolderId
                    ? `New project in "${currentFolder?.name}"`
                    : "Start a new project in your workspace"}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsProjectModalOpen(false)}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4 pt-1">
              <div>
                <label className="text-xs font-medium text-gray-400 block mb-1.5">
                  Project Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Grak AI, Voice Assistant, Next.js App..."
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full bg-[#16151c] border border-white/10 rounded-2xl px-4 py-3 text-sm text-white placeholder-gray-500 outline-none focus:border-blue-500/80 transition-colors"
                  autoFocus
                />
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsProjectModalOpen(false)}
                  className="w-full py-2.5 rounded-2xl text-xs font-semibold text-white bg-transparent border border-white/15 hover:bg-white/10 transition-colors cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-full py-2.5 rounded-2xl text-xs font-semibold transition-all cursor-pointer bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/30 active:scale-[0.98]"
                >
                  Create project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 3. Add Existing Project Modal                            */}
      {/* ======================================================== */}
      {isAddExistingProjectModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-150"
          onClick={() => setIsAddExistingProjectModalOpen(false)}
        >
          <div
            className="w-full max-w-md bg-[#1e1d24] border border-white/10 rounded-3xl p-6 shadow-2xl text-gray-200 space-y-4 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white tracking-tight">
                  Add existing project
                </h3>
                <p className="text-xs text-gray-400 mt-1">
                  Select a project to add to "{currentFolder?.name}"
                </p>
              </div>
              <button
                type="button"
                onClick={() => setIsAddExistingProjectModalOpen(false)}
                className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
              {candidateProjectsToAdd.length === 0 ? (
                <div className="text-center py-6 text-xs text-gray-500">
                  No other projects available. Create a new one instead!
                </div>
              ) : (
                candidateProjectsToAdd.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => handleAddProjectToCurrentFolder(p.id)}
                    className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="w-7 h-7 rounded-full bg-[#8c6b54] text-white font-semibold text-xs flex items-center justify-center shrink-0">
                        {userInitial}
                      </div>
                      <span className="text-xs font-semibold text-white truncate">
                        {p.name}
                      </span>
                    </div>
                    <span className="text-xs text-blue-400 hover:text-blue-300 font-medium">
                      Add
                    </span>
                  </div>
                ))
              )}
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={() => setIsAddExistingProjectModalOpen(false)}
                className="w-full py-2.5 rounded-2xl text-xs font-semibold text-white bg-transparent border border-white/15 hover:bg-white/10 transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
