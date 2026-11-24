import "./globals.css";

// Using standard system fonts fallback instead of next/font/google to avoid Turbopack build errors
const interVariable = "--font-inter";
const newsreaderVariable = "--font-newsreader";

export const metadata = {
  title: "Grak AI",
  description: "The intelligent assistant for modern startups.",
};

import { Providers } from "./providers";
import AuthGuard from "../components/AuthGuard";

export default function RootLayout({ children, modal }) {
  return (
    <html
      lang="en"
      className={`${interVariable} ${newsreaderVariable} font-sans`}
    >
      <body className="bg-black text-white antialiased">
        <Providers>
          <AuthGuard>
            {children}
            {modal}
          </AuthGuard>
        </Providers>
      </body>
    </html>
  );
}
