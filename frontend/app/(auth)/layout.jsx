import React from "react";
import TopNav from "@/components/landing/TopNav";
import AuthShowcasePanel from "@/components/AuthShowcasePanel";

export default function AuthLayout({ children }) {
  return (
    <div className="min-h-screen bg-[#F5F5F7] text-gray-900 dark:bg-black dark:text-white flex flex-col lg:flex-row relative">
      <TopNav />

      {/* Left Pane - Content & Forms */}
      <div className="w-full lg:w-1/2 flex flex-col relative z-10 px-8 lg:px-16 pb-8 lg:pb-16 pt-28 lg:pt-36 bg-transparent">
        {/* Main Content Area */}
        <main className="flex-1 flex flex-col justify-start max-w-md w-full mx-auto">
          <div className="mb-8 text-center flex flex-col items-center">
            <h1 className="text-4xl lg:text-5xl font-serif font-medium tracking-tight mb-4 text-gray-900 dark:text-white leading-tight">
              Smarter AI,
              <br />
              Better Results.
            </h1>
            <p className="text-gray-900 dark:text-gray-300 text-[17px] font-serif font-medium max-w-sm">
              Bring any idea to life with Grak AI. Secure, fast, and scalable.
            </p>
          </div>

          {/* Auth Form Container */}
          <div className="w-full relative z-20">{children}</div>
        </main>
      </div>

      {/* Right Pane - Visuals (Showcase Panel) */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center relative z-10 px-6 lg:px-6 xl:px-8 pb-12 lg:pb-16 pt-4 lg:pt-36 bg-transparent">
        <AuthShowcasePanel />
      </div>
    </div>
  );
}
