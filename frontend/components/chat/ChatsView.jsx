"use client";
import React, { useState } from "react";
import {
  Search,
  ChevronDown,
  Plus,
  MessageSquare,
  Diamond,
  ArrowRight,
} from "lucide-react";

export default function ChatsView({
  conversations = [],
  onSelectConversation,
  onNewChat,
}) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const filtered = conversations.filter((c) =>
    (c.title || "New chat").toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="flex-1 h-full overflow-y-auto px-6 py-8 md:px-12 md:py-10 text-gray-200 bg-[#0c0b10] relative z-10">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between pb-2">
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Chats
          </h1>
          <button
            type="button"
            onClick={onNewChat}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-full text-xs font-semibold shadow-md shadow-blue-900/30 transition-all cursor-pointer active:scale-95"
          >
            <span>New chat</span>
          </button>
        </div>

        {/* Search Bar & Filter */}
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <Search
              size={14}
              className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400"
            />
            <input
              type="text"
              placeholder="Search chats..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#181720]/80 border border-white/10 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-gray-500 outline-none focus:border-white/20 transition-colors"
            />
          </div>

          <button
            type="button"
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#181720]/80 border border-white/10 text-xs font-medium text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            <span>{filter}</span>
            <ChevronDown size={13} className="text-gray-400" />
          </button>
        </div>

        {/* Chats List */}
        <div className="space-y-2 pt-2">
          {filtered.map((conv, idx) => {
            const timeAgo =
              idx === 0
                ? "9 hours ago"
                : idx === 1
                  ? "10 hours ago"
                  : "Earlier";
            const projectTag = idx === 0 ? "Jarvis AI Hub" : null;

            return (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className="group flex items-center justify-between p-4 rounded-2xl bg-[#15141c]/60 hover:bg-[#1b1a24] border border-white/5 hover:border-white/10 transition-all cursor-pointer"
              >
                <div className="flex flex-col min-w-0 pr-4">
                  <div className="flex items-center gap-2.5 mb-1">
                    <span className="font-semibold text-white text-sm group-hover:text-blue-400 transition-colors truncate">
                      {conv.title || "New chat"}
                    </span>
                    {/* Blue active dot indicator from screenshot */}
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                  </div>
                  <span className="text-xs text-gray-400">{timeAgo}</span>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  {projectTag && (
                    <span className="px-3 py-1 rounded-full text-[11px] font-medium bg-white/10 text-gray-300 border border-white/5">
                      {projectTag}
                    </span>
                  )}
                  <ArrowRight
                    size={14}
                    className="text-gray-500 group-hover:text-white group-hover:translate-x-0.5 transition-all opacity-0 group-hover:opacity-100"
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
