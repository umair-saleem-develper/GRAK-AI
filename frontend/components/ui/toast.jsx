"use client";
import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// A simple local state manager for toasts would go here,
// but for the atomic component we just provide the UI.

export function Toast({ title, description, variant = "default", onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={cn(
        "glass-card p-4 pr-8 rounded-xl shadow-xl flex flex-col gap-1 relative min-w-[300px]",
        variant === "destructive" ? "border-red-500/30 bg-red-500/10" : "",
      )}
    >
      <div
        className={cn(
          "font-medium text-sm",
          variant === "destructive" ? "text-red-400" : "text-white",
        )}
      >
        {title}
      </div>
      {description && (
        <div className="text-xs text-muted-foreground">{description}</div>
      )}
      <button
        onClick={onClose}
        className="absolute top-3 right-3 text-gray-500 hover:text-white"
      >
        ✕
      </button>
    </motion.div>
  );
}
