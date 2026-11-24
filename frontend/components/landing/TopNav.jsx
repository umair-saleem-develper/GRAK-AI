"use client";
import React from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";

export default function TopNav() {
  return (
    <header className="flex items-center justify-between w-full py-6 px-8 absolute top-0 left-0 z-50">
      <div className="flex items-center">
        <Link
          href="/"
          className="flex items-center gap-3 transition-opacity hover:opacity-80"
        >
          <div className="w-14 h-14 flex items-center justify-center relative shrink-0">
            <Image
              src="/grak-logo-light-new.png"
              alt="Grak AI"
              width={96}
              height={96}
              className="object-contain dark:hidden"
              priority
            />
            <Image
              src="/grak-logo-dark.png"
              alt="Grak AI"
              width={96}
              height={96}
              className="object-contain hidden dark:block scale-125 drop-shadow-md"
              priority
            />
          </div>
          <span className="text-[26px] font-serif font-medium tracking-tight text-gray-900 dark:text-white mt-2">
            Grak AI
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={() => window.dispatchEvent(new CustomEvent("highlightAuth"))}
          className="rounded-xl font-medium text-[15px] px-4 py-2 bg-[#191919] dark:bg-[#F5F5F5] text-white dark:text-[#191919] hover:bg-black dark:hover:bg-white transition-colors"
        >
          Try Grak AI
        </button>
      </div>
    </header>
  );
}
