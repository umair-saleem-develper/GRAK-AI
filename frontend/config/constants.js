export const APP_CONFIG = {
  api: {
    baseUrl: (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/+$/, ""),
    endpoints: {
      stream: "/api/chat/stream",
      upload: "/api/uploads",
      conversations: "/api/conversations",
      auth: {
        firebase: "/api/auth/firebase",
        refresh: "/api/auth/refresh",
        logout: "/api/auth/logout",
        me: "/api/auth/me",
      },
    },
  },
  features: {
    voice: true,
    vision: true,
    agents: true,
    memory: true,
    search: true,
  },
};
