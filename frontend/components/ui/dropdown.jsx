"use client";
import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export function Dropdown({
  trigger,
  children,
  isOpen,
  onClose,
  align = "right",
  className,
}) {
  return (
    <div className="relative inline-block text-left">
      <div>{trigger}</div>
      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={onClose}></div>
            <motion.div
              initial={{ opacity: 0, y: -5, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -5, scale: 0.95 }}
              transition={{ duration: 0.15 }}
              className={cn(
                "absolute z-50 mt-2 w-56 rounded-xl border border-white/10 bg-[#1f1e24] shadow-xl backdrop-blur-xl",
                align === "right" ? "right-0" : "left-0",
                className,
              )}
            >
              <div className="py-1">{children}</div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export function DropdownItem({
  children,
  onClick,
  className,
  destructive = false,
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "block w-full px-4 py-2 text-sm text-left transition-colors",
        destructive
          ? "text-red-400 hover:bg-red-500/10"
          : "text-gray-200 hover:bg-white/10 hover:text-white",
        className,
      )}
    >
      {children}
    </button>
  );
}
