"use client";

import { useAuth } from "../context/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";

export default function AuthGuard({ children }) {
  const { session, status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status !== "initializing") {
      if (
        status === "unauthenticated" &&
        !["/login", "/register"].includes(pathname)
      ) {
        console.log(
          `[DEBUG] AuthGuard: status is ${status}. Redirecting to /login from ${pathname}`,
        );
        router.push("/login");
      } else if (
        status === "authenticated" &&
        ["/login", "/register"].includes(pathname)
      ) {
        console.log(
          `[DEBUG] AuthGuard: status is ${status}. Redirecting to / from ${pathname}`,
        );
        router.push("/");
      } else {
        console.log(
          `[DEBUG] AuthGuard: status is ${status}. Permitting navigation to ${pathname}`,
        );
      }
    }
  }, [status, router, pathname]);

  if (status === "initializing") {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
      </div>
    );
  }

  // If user is authenticated (or offline but has a session), do not render auth pages
  if (
    status !== "unauthenticated" &&
    ["/login", "/register"].includes(pathname)
  ) {
    return null;
  }

  // If user is truly unauthenticated, do not render protected routes
  if (
    status === "unauthenticated" &&
    !["/login", "/register"].includes(pathname)
  ) {
    return null;
  }

  return children;
}
