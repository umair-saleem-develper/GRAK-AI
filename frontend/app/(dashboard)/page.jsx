"use client";
import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useSpring,
} from "framer-motion";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import Sidebar from "@/components/chat/Sidebar";
import ChatArea from "@/components/chat/ChatArea";
import MessageInput from "@/components/chat/MessageInput";
import ConnectorsModal from "@/components/chat/ConnectorsModal";
import SearchModal from "@/components/chat/SearchModal";
import ChatsView from "@/components/chat/ChatsView";
import ProjectsView from "@/components/chat/ProjectsView";
import { StreamClient } from "@/lib/streamClient";
import { fetchWithAuth } from "@/lib/apiClient";
import {
  PanelLeftOpen,
  ChevronDown,
  Activity,
  LogOut,
  LayoutGrid,
  X,
  ArrowDown,
} from "lucide-react";
import AuthGuard from "@/components/AuthGuard";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const queryClient = useQueryClient();
  const { session, logout } = useAuth();

  const rawName =
    session?.user?.name ||
    session?.user?.first_name ||
    session?.user?.email?.split("@")[0] ||
    "there";
  // Remove numbers and special characters, replace with space, and grab the first alphabetical chunk
  const cleanName =
    rawName
      .replace(/[^a-zA-Z]/g, " ")
      .trim()
      .split(/\s+/)[0] || "there";
  const firstName = cleanName.charAt(0).toUpperCase() + cleanName.slice(1);

  const [greetingIndex, setGreetingIndex] = useState(0);

  const greetings = [
    `What can I help with, ${firstName}?`,
    `What's the vibe, ${firstName}?`,
    `Hi ${firstName}, let's get into it`,
  ];

  useEffect(() => {
    setGreetingIndex(Math.floor(Math.random() * greetings.length));
    const interval = setInterval(() => {
      setGreetingIndex((prev) => (prev + 1) % greetings.length);
    }, 15000);
    return () => clearInterval(interval);
  }, [greetings.length]);

  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  // "chat" | "chats" | "projects"
  const [currentView, setCurrentView] = useState("chat");
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Active Project Context (when user is creating or exploring a project)
  const [activeProject, setActiveProject] = useState(null);
  const activeProjectRef = useRef(null);
  useEffect(() => {
    activeProjectRef.current = activeProject;
  }, [activeProject]);

  // Projects & Folders synced from localStorage
  const [projects, setProjects] = useState([]);
  const [folders, setFolders] = useState([]);

  // Load projects and folders on mount and listen for changes
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
    window.addEventListener("grak-folder-updated", handleEvent);
    window.addEventListener("storage", loadItems);

    return () => {
      window.removeEventListener("grak-project-created", handleEvent);
      window.removeEventListener("grak-project-deleted", handleEvent);
      window.removeEventListener("grak-folder-created", handleEvent);
      window.removeEventListener("grak-folder-deleted", handleEvent);
      window.removeEventListener("grak-folder-updated", handleEvent);
      window.removeEventListener("storage", loadItems);
    };
  }, []);

  // Auto-collapse sidebar on small mobile screens and on resize
  useEffect(() => {
    const handleResize = () => {
      if (typeof window !== "undefined" && window.innerWidth < 768) {
        setIsSidebarOpen(false);
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Allow other components (like MessageInput project creation) to open sidebar
  useEffect(() => {
    const handleOpenSidebar = () => setIsSidebarOpen(true);
    window.addEventListener("open-sidebar", handleOpenSidebar);
    return () => window.removeEventListener("open-sidebar", handleOpenSidebar);
  }, []);

  // Initialize from URL query params safely on client side
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const c = params.get("c");
      if (c) setActiveConversationId(c);
    }
  }, []);

  // Streaming state
  const [isGenerating, setIsGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingMsgId, setStreamingMsgId] = useState(null);
  const [pendingUserMsg, setPendingUserMsg] = useState(null);
  const [streamingProviderInfo, setStreamingProviderInfo] = useState(null);
  const streamingProviderInfoRef = useRef(null);
  const streamClientRef = useRef(null);
  const streamingContentRef = useRef("");

  // Event Log Panel state (collapsible, hidden by default)
  const [isEventLogOpen, setIsEventLogOpen] = useState(false);
  const [eventLogs, setEventLogs] = useState([]);
  const chunksCountRef = useRef(0);

  // Reference layout scroller and composer measurement
  const scrollerRef = useRef(null);
  const composerContainerRef = useRef(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const [activeZoomImage, setActiveZoomImage] = useState(null);

  // ResizeObserver to write --composer-h dynamically
  useEffect(() => {
    const el = composerContainerRef.current;
    if (!el) return;

    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const height =
          entry.borderBoxSize?.[0]?.blockSize ?? entry.contentRect.height;
        if (height > 0) {
          document.documentElement.style.setProperty(
            "--composer-h",
            `${Math.round(height)}px`,
          );
        }
      }
    });

    ro.observe(el);
    return () => ro.disconnect();
  }, [currentView, activeConversationId]);

  // Handle scroll events to show/hide scroll-to-bottom button
  const handleScroll = () => {
    if (!scrollerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollerRef.current;
    const distanceToBottom = scrollHeight - (scrollTop + clientHeight);
    setShowScrollBottom(distanceToBottom > 150);
  };

  const scrollToBottom = () => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTo({
        top: scrollerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  // Fetch messages for active conversation
  const { data: conversationData, isLoading: isLoadingMessages } = useQuery({
    queryKey: ["conversation", activeConversationId],
    queryFn: async () => {
      if (!activeConversationId) return { messages: [] };
      const res = await fetchWithAuth(
        `/api/conversations/${activeConversationId}`,
      );
      if (!res.ok) throw new Error("Failed to fetch conversation");
      return res.json();
    },
    enabled: !!activeConversationId && !isGenerating,
  });

  // Fetch conversations list (for ChatsView, SearchModal, Sidebar recents)
  const { data: convData } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      const res = await fetchWithAuth("/api/conversations");
      if (!res.ok) throw new Error("Failed to fetch conversations");
      return res.json();
    },
  });

  const messages = conversationData?.messages || [];

  const handleNewChat = () => {
    setActiveConversationId(null);
    setCurrentView("chat");
    if (typeof window !== "undefined") window.history.pushState(null, "", "/");
    setStreamingContent("");
    streamingContentRef.current = "";
    setPendingUserMsg(null);
  };

  const handleSelectConversation = (id) => {
    if (isGenerating) return; // Prevent switching while generating
    setActiveConversationId(id);
    setCurrentView("chat");
    if (typeof window !== "undefined")
      window.history.pushState(null, "", `/?c=${id}`);
    setStreamingContent("");
    streamingContentRef.current = "";
    setPendingUserMsg(null);
  };

  const handleSelectProject = (proj) => {
    setActiveProject(proj);
    setCurrentView("chat");
    if (proj.conversationId) {
      handleSelectConversation(proj.conversationId);
    } else {
      handleNewChat();
    }
  };

  const handleStop = () => {
    if (streamClientRef.current) {
      streamClientRef.current.abort();
      setIsGenerating(false);
    }
  };

  const handleSendMessage = async (
    content,
    uploadedText,
    imageBase64,
    mode = null,
  ) => {
    setIsGenerating(true);
    setStreamingContent("");
    streamingContentRef.current = "";
    setStreamingProviderInfo(null);
    streamingProviderInfoRef.current = null;
    chunksCountRef.current = 0;
    const tempId = `temp_${Date.now()}`;
    setStreamingMsgId(tempId);

    // Log stream initiation (Requirement 3)
    setEventLogs((prev) => [
      ...prev,
      {
        timestamp: new Date().toLocaleTimeString(),
        type: "init",
        details: "Chat stream initiated",
      },
    ]);

    // Optimistically update the UI with user message
    const userMsg = {
      id: `user_${Date.now()}`,
      role: "user",
      content: content,
    };
    if (uploadedText) {
      userMsg.content = `Attached Document Context:\n${uploadedText}\n\nUser Message: ${content}`;
    }

    // If we have an active conversation, append to it in cache
    if (activeConversationId) {
      queryClient.setQueryData(
        ["conversation", activeConversationId],
        (old) => {
          if (!old) return { messages: [userMsg] };
          return { ...old, messages: [...old.messages, userMsg] };
        },
      );
    } else {
      setPendingUserMsg(userMsg);
    }

    let currentConvId = activeConversationId;

    const payload = {
      conversation_id: currentConvId,
      content,
      uploaded_text: uploadedText,
      image_base64: imageBase64,
      mode: mode || undefined,
    };

    // Note: using /api/chat/stream which is the locked backend streaming endpoint
    const client = new StreamClient(
      "/api/chat/stream",
      // onChunk
      (chunkText) => {
        setStreamingContent((prev) => {
          const newVal = prev + chunkText;
          streamingContentRef.current = newVal;
          return newVal;
        });

        // Track chunk count so far instead of logging every chunk (Requirement 3)
        chunksCountRef.current += 1;
        const currentCount = chunksCountRef.current;
        setEventLogs((prev) => {
          const chunkEntryIdx = prev.findIndex((e) => e.type === "chunk_count");
          const updatedEntry = {
            timestamp: new Date().toLocaleTimeString(),
            type: "chunk_count",
            details: `${currentCount} chunks received so far`,
          };
          if (chunkEntryIdx >= 0) {
            const nextLogs = [...prev];
            nextLogs[chunkEntryIdx] = updatedEntry;
            return nextLogs;
          }
          return [...prev, updatedEntry];
        });
      },
      // onMeta (Server gives us the conversation_id, crucial for lazy init)
      (meta) => {
        setEventLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            type: "meta",
            details: `conversation_id: ${meta.conversation_id}`,
          },
        ]);

        if (meta.conversation_id && !currentConvId) {
          currentConvId = meta.conversation_id;

          // Seed the new conversation cache with the optimistic user message
          queryClient.setQueryData(["conversation", currentConvId], {
            messages: [userMsg],
          });
          setPendingUserMsg(null);

          setActiveConversationId(currentConvId);
          // Shallow update the URL to prevent React unmounts
          if (typeof window !== "undefined") {
            window.history.pushState(null, "", `/?c=${currentConvId}`);
          }

          // Link conversation to active project if present
          const currentActive = activeProjectRef.current;
          if (currentActive) {
            setProjects((prev) => {
              const updated = prev.map((p) =>
                p.id === currentActive.id
                  ? { ...p, conversationId: currentConvId }
                  : p,
              );
              try {
                localStorage.setItem("grak_projects", JSON.stringify(updated));
              } catch (e) {}
              return updated;
            });
            setActiveProject((prev) =>
              prev ? { ...prev, conversationId: currentConvId } : null,
            );
          }

          // Invalidate sidebar to show the new chat
          queryClient.invalidateQueries(["conversations"]);
        }
      },
      // onError
      (error) => {
        console.warn("Stream Error:", error.message);
        setEventLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            type: "error",
            details: error.message || "Stream error occurred",
          },
        ]);
        setIsGenerating(false);
        if (error.message && error.message.includes("401")) {
          // Token expired or invalid, trigger a reload to let AuthGuard handle redirect to login
          window.location.reload();
          return;
        }
        // Refresh to show failure message saved in DB
        if (currentConvId)
          queryClient.invalidateQueries(["conversation", currentConvId]);
      },
      // onDone
      () => {
        setEventLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            type: "done",
            details: `Stream completed (${chunksCountRef.current} chunks total)`,
          },
        ]);

        // Optimistically lock the AI message into the cache before we invalidate,
        // so it doesn't vanish while React Query re-fetches the conversation!
        if (currentConvId) {
          queryClient.setQueryData(["conversation", currentConvId], (old) => {
            if (!old) return old;
            const assistantMsg = {
              id: tempId,
              role: "assistant",
              content: streamingContentRef.current,
              provider: streamingProviderInfoRef.current?.provider || "gemini",
              fallback: streamingProviderInfoRef.current?.fallback || false,
            };
            return { ...old, messages: [...old.messages, assistantMsg] };
          });
        }

        setIsGenerating(false);
        setPendingUserMsg(null);
        // Fully invalidate to pull the final assistant message from DB with accurate tokens/model
        if (currentConvId)
          queryClient.invalidateQueries(["conversation", currentConvId]);
      },
      // onProvider — logs which model/provider made the image; never shown in UI
      (providerEvent) => {
        const info = {
          provider: providerEvent.provider,
          fallback: !!providerEvent.fallback,
        };
        setStreamingProviderInfo(info);
        streamingProviderInfoRef.current = info;
        // DEBUG: paste this in DevTools to verify provider per image
        console.debug(
          `[Grak AI] Image provider=${info.provider} fallback=${info.fallback}`,
        );
        setEventLogs((prev) => [
          ...prev,
          {
            timestamp: new Date().toLocaleTimeString(),
            type: "provider",
            details: `provider: ${info.provider}, fallback: ${info.fallback}`,
          },
        ]);
      },
    );

    streamClientRef.current = client;
    client.connect(payload);
  };

  // Cursor Glow state
  const mouseX = useMotionValue(
    typeof window !== "undefined" ? window.innerWidth / 2 : 0,
  );
  const mouseY = useMotionValue(
    typeof window !== "undefined" ? window.innerHeight / 2 : 0,
  );

  const springConfig = { damping: 20, stiffness: 200, mass: 0.5 };
  const glowX = useSpring(mouseX, springConfig);
  const glowY = useSpring(mouseY, springConfig);

  const handleMouseMove = (e) => {
    mouseX.set(e.clientX);
    mouseY.set(e.clientY);
  };

  // Combine DB messages with currently streaming message
  const displayMessages = [...messages];
  if (
    pendingUserMsg &&
    !displayMessages.find((m) => m.id === pendingUserMsg.id)
  ) {
    displayMessages.push(pendingUserMsg);
  }
  if (isGenerating) {
    displayMessages.push({
      id: streamingMsgId,
      role: "assistant",
      content: streamingContent,
      provider: streamingProviderInfo?.provider,
      fallback: streamingProviderInfo?.fallback,
    });
  }

  const isEmpty = !activeConversationId && displayMessages.length === 0;

  return (
    <AuthGuard>
      <div
        className="flex h-dvh bg-[var(--chat-bg,#0b0a0f)] text-gray-900 dark:text-gray-100 font-sans overflow-hidden relative"
        onMouseMove={handleMouseMove}
      >
        {/* Interactive Rotating Cursor Glow - exact same deep purple gradient as login showcase */}
        <AnimatePresence>
          {isEmpty && currentView === "chat" && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.6 }}
              className="absolute w-[800px] h-[800px] md:w-[960px] md:h-[960px] rounded-full pointer-events-none z-0 overflow-visible"
              style={{
                left: glowX,
                top: glowY,
                x: "-50%",
                y: "-50%",
              }}
            >
              <div className="grak-dashboard-orb w-full h-full rounded-full blur-[80px] md:blur-[120px] opacity-90 dark:opacity-85" />
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isSidebarOpen && (
            <Sidebar
              activeConversationId={activeConversationId}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
              onClose={() => setIsSidebarOpen(false)}
              currentView={currentView}
              onSelectView={(view) => setCurrentView(view)}
              onOpenSearch={() => setIsSearchOpen(true)}
            />
          )}
        </AnimatePresence>

        <div className="flex-1 flex flex-col min-w-0 bg-transparent relative z-10">
          {/* Header */}
          <header className="h-14 border-b border-transparent flex items-center justify-between px-6 shrink-0 bg-transparent z-10 transition-colors">
            <div className="flex items-center gap-3">
              <AnimatePresence>
                {!isSidebarOpen && (
                  <motion.button
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    transition={{ duration: 0.2 }}
                    onClick={() => setIsSidebarOpen(true)}
                    className="rounded-xl hover:bg-black/5 dark:hover:bg-white/5 transition-colors flex items-center justify-center shrink-0 group relative w-10 h-10"
                  >
                    {/* Logo - visible normally, hides on hover */}
                    <div className="w-10 h-10 flex items-center justify-center transition-opacity duration-200 group-hover:opacity-0 absolute inset-0 m-auto">
                      <Image
                        src="/grak-logo-light-transparent.png"
                        alt=""
                        width={96}
                        height={96}
                        className="object-contain dark:hidden mix-blend-multiply"
                        priority
                      />
                      <Image
                        src="/grak-logo-dark.png"
                        alt=""
                        width={96}
                        height={96}
                        className="object-contain hidden dark:block scale-125 drop-shadow-md"
                        priority
                      />
                    </div>
                    {/* Sidebar Open Icon - hidden normally, shows on hover */}
                    <div className="w-8 h-8 absolute inset-0 m-auto flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <PanelLeftOpen
                        size={22}
                        className="text-gray-600 dark:text-gray-300"
                      />
                    </div>
                  </motion.button>
                )}
              </AnimatePresence>
              <motion.div
                initial={false}
                animate={{ opacity: isSidebarOpen ? 0 : 1 }}
                transition={{ duration: 0.2 }}
                className="flex items-center transition-colors"
              >
                <h1 className="text-[26px] font-serif font-medium tracking-tight text-black dark:text-white mt-2">
                  Grak
                </h1>
              </motion.div>
              {activeProject && (
                <div className="flex items-center gap-1 ml-2">
                  <span className="text-gray-400 dark:text-gray-600">/</span>
                  <span className="px-2.5 py-1 bg-purple-500/10 text-purple-400 text-xs rounded-lg font-medium border border-purple-500/20 flex items-center gap-1.5 shadow-sm">
                    <LayoutGrid size={11} className="text-purple-400" />
                    <span className="max-w-[120px] truncate">
                      {activeProject.name}
                    </span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveProject(null);
                      }}
                      className="hover:text-white text-purple-300 ml-0.5 transition-colors cursor-pointer"
                      title="Exit project"
                    >
                      <X size={11} />
                    </button>
                  </span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-3">
              <button className="flex items-center gap-2 bg-[#004a77] hover:bg-[#005a8f] text-blue-100 px-4 py-1.5 rounded-full text-[13px] font-medium transition-colors border border-blue-400/20 shadow-sm">
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-blue-300"
                >
                  <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
                  <path d="M20 3v4" />
                  <path d="M22 5h-4" />
                  <path d="M4 17v2" />
                  <path d="M5 18H3" />
                </svg>
                Upgrade
              </button>

              {/* Instant Logout button */}
              <button
                type="button"
                onClick={() => logout()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium text-gray-400 bg-black/5 dark:bg-white/5 border border-black/5 dark:border-white/5 hover:bg-red-800 hover:text-white hover:border-red-700 dark:hover:bg-red-800/90 dark:hover:text-white dark:hover:border-red-700/80 transition-all duration-200 cursor-pointer shadow-sm hover:shadow-red-950/40"
                title="Log out"
              >
                <LogOut size={13} />
                <span>Log out</span>
              </button>
            </div>
          </header>



          {/* === MAIN CONTENT AREA — switches based on currentView === */}
          {currentView === "chats" ? (
            <ChatsView
              conversations={convData?.items || convData?.conversations || []}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
            />
          ) : currentView === "projects" ? (
            <ProjectsView
              projects={projects}
              folders={folders}
              userName={rawName}
              userInitial={(session?.user?.email || "M")
                .charAt(0)
                .toUpperCase()}
              onCreateProject={(name, folderId = null) => {
                const newProj = {
                  id: "proj_" + Date.now(),
                  name,
                  folderId: folderId || null,
                  createdAt: new Date().toISOString(),
                  conversationId: null,
                };
                const updated = [newProj, ...projects];
                setProjects(updated);
                setActiveProject(newProj);
                try {
                  localStorage.setItem(
                    "grak_projects",
                    JSON.stringify(updated),
                  );
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-project-created", { detail: newProj }),
                );

                // Directly switch to new chat!
                handleNewChat();
                setCurrentView("chat");
              }}
              onSelectProject={handleSelectProject}
              onUpdateProject={(projId, updates) => {
                const updated = projects.map((p) =>
                  p.id === projId ? { ...p, ...updates } : p,
                );
                setProjects(updated);
                try {
                  localStorage.setItem(
                    "grak_projects",
                    JSON.stringify(updated),
                  );
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-project-updated", {
                    detail: { id: projId, updates },
                  }),
                );
              }}
              onDeleteProject={(projId) => {
                const updated = projects.filter((p) => p.id !== projId);
                setProjects(updated);
                if (activeProject?.id === projId) setActiveProject(null);
                try {
                  localStorage.setItem(
                    "grak_projects",
                    JSON.stringify(updated),
                  );
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-project-deleted", {
                    detail: { id: projId },
                  }),
                );
              }}
              onCreateFolder={(folderData) => {
                const newFolder = {
                  id: "folder_" + Date.now(),
                  name: folderData.name,
                  parentId: folderData.parentId || null,
                  visibility: "workspace",
                  createdAt: new Date().toISOString(),
                };
                const updated = [newFolder, ...folders];
                setFolders(updated);
                try {
                  localStorage.setItem("grak_folders", JSON.stringify(updated));
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-folder-created", { detail: newFolder }),
                );
              }}
              onDeleteFolder={(folderId) => {
                const updated = folders.filter((f) => f.id !== folderId);
                setFolders(updated);
                try {
                  localStorage.setItem("grak_folders", JSON.stringify(updated));
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-folder-deleted", {
                    detail: { id: folderId },
                  }),
                );
              }}
              onUpdateFolder={(folderId, updates) => {
                const updated = folders.map((f) =>
                  f.id === folderId ? { ...f, ...updates } : f,
                );
                setFolders(updated);
                try {
                  localStorage.setItem("grak_folders", JSON.stringify(updated));
                } catch (e) {
                  console.warn(e);
                }
                window.dispatchEvent(
                  new CustomEvent("grak-folder-updated", {
                    detail: { id: folderId, updates },
                  }),
                );
              }}
            />
          ) : isEmpty ? (
            <div className="flex-1 flex flex-col items-center justify-center px-4 pb-32 md:pb-[20vh]">
              <div className="relative w-full max-w-3xl flex flex-col items-center">
                <div className="h-12 mb-8 relative flex items-center justify-center w-full z-10">
                  <AnimatePresence mode="wait">
                    <motion.h2
                      key={greetingIndex}
                      initial={{ y: 10, opacity: 0 }}
                      animate={{ y: 0, opacity: 1 }}
                      exit={{ y: -10, opacity: 0 }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                      className="text-[32px] md:text-[40px] font-serif font-normal text-gray-900 dark:text-white text-center absolute w-full px-4 break-words"
                    >
                      {greetings[greetingIndex]}
                    </motion.h2>
                  </AnimatePresence>
                </div>
                <div className="w-full max-w-3xl px-4 relative z-10">
                  <MessageInput
                    onSendMessage={handleSendMessage}
                    isGenerating={isGenerating}
                    onStop={handleStop}
                    isEmpty={isEmpty}
                  />
                  <p className="mt-2 text-center text-xs text-white/40">
                    Grak AI can make mistakes.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="relative flex-1 h-full min-h-0 overflow-hidden">
              {/* Scroll area = FULL height behind the composer */}
              <div
                id="scroller"
                ref={scrollerRef}
                onScroll={handleScroll}
                className="h-full overflow-y-auto"
                style={{
                  paddingBottom: "calc(var(--composer-h, 110px) + 24px)",
                }}
              >
                <div className="mx-auto w-full max-w-3xl px-4">
                  <ChatArea
                    messages={displayMessages}
                    isGenerating={isGenerating}
                    zoomImage={activeZoomImage}
                    setZoomImage={setActiveZoomImage}
                  />
                </div>
              </div>

              {/* Scroll-to-bottom button: 36px circle, centered just above the composer */}
              <AnimatePresence>
                {showScrollBottom && (
                  <motion.button
                    initial={{ opacity: 0, y: 10, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.9 }}
                    transition={{ duration: 0.2 }}
                    type="button"
                    onClick={scrollToBottom}
                    className="absolute left-1/2 -translate-x-1/2 z-30 w-9 h-9 rounded-full bg-[var(--chat-bg,#0b0a0f)] border border-white/20 text-white shadow-xl flex items-center justify-center hover:bg-white/10 hover:border-white/30 transition-all cursor-pointer"
                    style={{
                      bottom: "calc(var(--composer-h, 110px) + 16px)",
                    }}
                    title="Scroll to bottom"
                  >
                    <ArrowDown size={17} />
                  </motion.button>
                )}
              </AnimatePresence>

              {/* Fixed bottom area with smooth fade zone + identical background composer wrapper */}
              <div className="absolute inset-x-0 bottom-0 pointer-events-none z-20">
                {/* 40px smooth fade zone: text passing behind composer fades out smoothly */}
                <div className="h-10 bg-gradient-to-t from-[var(--chat-bg,#0b0a0f)] to-transparent" />

                {/* Composer wrapper: SAME bg as chat, no border-top, no shadow, exact same max-w-3xl */}
                <div
                  ref={composerContainerRef}
                  className="bg-[var(--chat-bg,#0b0a0f)] px-4 pb-3 pointer-events-auto"
                  style={{
                    paddingBottom: "max(12px, env(safe-area-inset-bottom))",
                  }}
                >
                  <div className="mx-auto w-full max-w-3xl">
                    <MessageInput
                      onSendMessage={handleSendMessage}
                      isGenerating={isGenerating}
                      onStop={handleStop}
                      isEmpty={isEmpty}
                    />
                    <p className="mt-2 text-center text-xs text-white/40">
                      Grak AI can make mistakes.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Component-scoped CSS for dashboard orb */}
        <style>{`
          .grak-dashboard-orb {
            background:
              radial-gradient(60% 45% at 50% 108%, #ffffff 0%, #e4d4ff 22%, rgba(168,85,247,0) 70%),
              radial-gradient(75% 55% at 50% 92%, #a855f7 0%, #7c3aed 38%, rgba(76,29,149,0.5) 75%),
              radial-gradient(45% 50% at 6% 60%, rgba(124,58,237,.55), transparent 70%),
              radial-gradient(45% 50% at 94% 60%, rgba(147,51,234,.55), transparent 70%),
              radial-gradient(40% 40% at 50% 15%, rgba(0,0,0,0.1) 0%, transparent 80%);
            animation: grak-dashboard-drift 14s ease-in-out infinite alternate;
          }
          .dark .grak-dashboard-orb {
            background:
              radial-gradient(60% 45% at 50% 108%, #ffffff 0%, #e4d4ff 22%, rgba(168,85,247,0) 70%),
              radial-gradient(75% 55% at 50% 92%, #a855f7 0%, #7c3aed 38%, rgba(76,29,149,0.9) 75%),
              radial-gradient(45% 50% at 6% 60%, rgba(124,58,237,.9), transparent 70%),
              radial-gradient(45% 50% at 94% 60%, rgba(147,51,234,.9), transparent 70%),
              radial-gradient(40% 40% at 50% 15%, #07040d 0%, transparent 80%);
          }
          @keyframes grak-dashboard-drift {
            0% { transform: scale(1) rotate(0deg); }
            50% { transform: scale(1.08) rotate(180deg); }
            100% { transform: scale(1) rotate(360deg); }
          }
          @media (prefers-reduced-motion: reduce) {
            .grak-dashboard-orb { animation: none; }
          }
        `}</style>

        {/* Global Connectors Modal — listens to open-connectors event */}
        <ConnectorsModal />

        {/* Search / Command Palette Modal */}
        <SearchModal
          isOpen={isSearchOpen}
          onClose={() => setIsSearchOpen(false)}
          conversations={convData?.items || convData?.conversations || []}
          projects={projects}
          folders={folders}
          onSelectConversation={handleSelectConversation}
          onSelectProject={handleSelectProject}
          onNavigateView={(view) => {
            setCurrentView(view === "dashboard" ? "chat" : view);
            setIsSearchOpen(false);
          }}
          onCreateProject={(name) => {
            if (name) {
              const newProj = {
                id: "proj_" + Date.now(),
                name,
                createdAt: new Date().toISOString(),
                conversationId: null,
              };
              const updated = [newProj, ...projects];
              setProjects(updated);
              setActiveProject(newProj);
              try {
                localStorage.setItem("grak_projects", JSON.stringify(updated));
              } catch (e) {
                console.warn(e);
              }
              window.dispatchEvent(
                new CustomEvent("grak-project-created", { detail: newProj }),
              );
              handleNewChat();
              setCurrentView("chat");
            } else {
              setCurrentView("projects");
            }
          }}
          userName={rawName}
        />
      </div>
    </AuthGuard>
  );
}
