export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

function parseJwt(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map(function (c) {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join(""),
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export async function fetchWithAuth(url, options = {}) {
  let token = null;
  let hasLoggedIn = false;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("access_token");
    hasLoggedIn = localStorage.getItem("has_logged_in") === "true";
  }

  let needsRefresh = false;

  // Do not proactively refresh if calling auth endpoints
  if (!url.includes("/api/auth/refresh") && !url.includes("/api/auth/logout")) {
    if (!token && hasLoggedIn) {
      console.log(
        "[DEBUG] API: Missing token but has_logged_in is true. Proactive refresh required.",
      );
      needsRefresh = true;
    } else if (token) {
      const decoded = parseJwt(token);
      if (decoded && decoded.exp) {
        const timeToExpiry = decoded.exp * 1000 - Date.now();
        if (timeToExpiry < 60000) {
          // Less than 1 minute remaining
          console.log(
            `[DEBUG] API: Token expires in ${Math.round(timeToExpiry / 1000)}s. Proactive refresh required.`,
          );
          needsRefresh = true;
        }
      } else if (!decoded) {
        console.log(
          "[DEBUG] API: Invalid token format. Proactive refresh required.",
        );
        needsRefresh = true;
      }
    }
  }

  // Handle Proactive Refresh BEFORE the actual fetch
  if (needsRefresh) {
    if (isRefreshing) {
      console.log(
        "[DEBUG] API: Already proactively refreshing. Queuing request for URL:",
        url,
      );
      token = await new Promise(function (resolve, reject) {
        failedQueue.push({ resolve, reject });
      });
    } else {
      isRefreshing = true;
      try {
        console.log(
          "[DEBUG] API: Attempting proactive refresh /api/auth/refresh",
        );
        const refreshResponse = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
        });

        console.log(
          `[DEBUG] API: Proactive refresh returned ${refreshResponse.status}`,
        );

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          token = data.data.access_token;

          if (typeof window !== "undefined") {
            localStorage.setItem("access_token", token);
          }
          processQueue(null, token);
        } else if (
          refreshResponse.status === 401 ||
          refreshResponse.status === 403
        ) {
          throw new Error("invalid_token");
        } else {
          throw new Error(`server_error_${refreshResponse.status}`);
        }
      } catch (err) {
        processQueue(err, null);
        if (err.message === "invalid_token") {
          if (typeof window !== "undefined") {
            localStorage.removeItem("access_token");
            window.dispatchEvent(new Event("auth-logout"));
          }
        }
        throw err; // Throw immediately so we don't attempt the fetch and get a 401
      } finally {
        isRefreshing = false;
      }
    }
  }

  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  options.credentials = "include"; // Essential for sending/receiving HttpOnly cookies

  // Use relative URL to leverage Next.js rewrite proxy (avoids SameSite=Strict cookie drops)
  let response = await fetch(url, {
    ...options,
    headers,
  });

  // Fallback Lazy Refresh (just in case backend rejects token anyway)
  if (
    response.status === 401 &&
    !url.includes("/api/auth/refresh") &&
    !url.includes("/api/auth/logout")
  ) {
    console.log("[DEBUG] API: Request unexpectedly returned 401. URL:", url);
    if (isRefreshing) {
      console.log(
        "[DEBUG] API: Already refreshing (lazy). Queuing request for URL:",
        url,
      );
      return new Promise(function (resolve, reject) {
        failedQueue.push({ resolve, reject });
      }).then((newToken) => {
        headers.set("Authorization", `Bearer ${newToken}`);
        console.log(
          "[DEBUG] API: Retrying queued request after lazy refresh. URL:",
          url,
        );
        return fetch(url, { ...options, headers });
      });
    }

    const originalRequest = options;
    isRefreshing = true;

    try {
      console.log("[DEBUG] API: attempting lazy refresh /api/auth/refresh");
      const refreshResponse = await fetch("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      console.log(
        `[DEBUG] API: lazy refresh returned ${refreshResponse.status}`,
      );

      if (refreshResponse.ok) {
        const data = await refreshResponse.json();
        const newAccessToken = data.data.access_token;

        if (typeof window !== "undefined") {
          localStorage.setItem("access_token", newAccessToken);
        }

        processQueue(null, newAccessToken);

        headers.set("Authorization", `Bearer ${newAccessToken}`);
        console.log(`[DEBUG] API: retrying original request (lazy). URL:`, url);
        response = await fetch(url, {
          ...originalRequest,
          headers,
        });
      } else if (
        refreshResponse.status === 401 ||
        refreshResponse.status === 403
      ) {
        throw new Error("invalid_token");
      } else {
        throw new Error(`server_error_${refreshResponse.status}`);
      }
    } catch (err) {
      processQueue(err, null);
      if (err.message === "invalid_token") {
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          window.dispatchEvent(new Event("auth-logout"));
        }
      }
      throw err;
    } finally {
      isRefreshing = false;
    }
  }

  return response;
}

if (typeof window !== "undefined") {
  window.fetchWithAuth = fetchWithAuth;
}
