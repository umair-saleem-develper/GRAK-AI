export class StreamClient {
  constructor(endpoint, onChunk, onMeta, onError, onDone, onProvider) {
    this.endpoint = endpoint;
    this.onChunk = onChunk;
    this.onMeta = onMeta;
    this.onError = onError;
    this.onDone = onDone;
    this.onProvider = onProvider;
    this.abortController = new AbortController();
    this.retryCount = 0;
    this.toastElement = null;
  }

  showToast() {
    if (typeof document === "undefined") return;

    const isColdStart = this.retryCount > 1;
    const message = isColdStart
      ? "Waking up AI backend (cold start)... please wait"
      : "Connecting to AI service...";

    if (!this.toastElement) {
      this.toastElement = document.createElement("div");
      this.toastElement.style.position = "fixed";
      this.toastElement.style.bottom = "20px";
      this.toastElement.style.right = "20px";
      this.toastElement.style.backgroundColor = "rgba(18, 17, 24, 0.95)";
      this.toastElement.style.color = "#f4f4f5";
      this.toastElement.style.border = "1px solid rgba(168, 85, 247, 0.35)";
      this.toastElement.style.padding = "10px 16px";
      this.toastElement.style.borderRadius = "10px";
      this.toastElement.style.fontSize = "13px";
      this.toastElement.style.fontWeight = "500";
      this.toastElement.style.boxShadow = "0 8px 30px rgba(0, 0, 0, 0.5)";
      this.toastElement.style.zIndex = "9999";
      this.toastElement.style.fontFamily = "sans-serif";
      this.toastElement.style.backdropFilter = "blur(8px)";
      this.toastElement.style.display = "flex";
      this.toastElement.style.alignItems = "center";
      this.toastElement.style.gap = "10px";
      document.body.appendChild(this.toastElement);
    }

    this.toastElement.innerHTML = `
      <svg class="animate-spin h-4 w-4 text-purple-400 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>${message}</span>
    `;
  }

  hideToast() {
    if (this.toastElement && this.toastElement.parentNode) {
      this.toastElement.parentNode.removeChild(this.toastElement);
      this.toastElement = null;
    }
  }

  async connect(body) {
    while (!this.abortController.signal.aborted) {
      try {
        const token = localStorage.getItem("access_token");
        const headers = {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const response = await fetch(this.endpoint, {
          method: "POST",
          headers: headers,
          body: JSON.stringify(body),
          signal: this.abortController.signal,
        });

        if (!response.ok) {
          // If we hit an error like 500, throw it to trigger backoff, unless it's a permanent error like 400.
          if (response.status >= 500 || response.status === 429) {
            throw new Error(`Transient HTTP error! status: ${response.status}`);
          } else {
            // For 400, 401, 403, etc., do not retry automatically.
            throw new Error(`Permanent HTTP error! status: ${response.status}`);
          }
        }

        // Connection successful, clear retry state and hide toast
        this.retryCount = 0;
        this.hideToast();

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        // eslint-disable-next-line no-constant-condition
        while (true) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // Process line by line
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // Keep the incomplete line in the buffer

          for (const line of lines) {
            if (line.trim() === "") continue;

            if (line.startsWith("data: ")) {
              const dataStr = line.substring(6).trim();
              if (dataStr === "[DONE]") {
                if (this.onDone) this.onDone();
                return; // End the connection loop completely
              }

              try {
                const parsed = JSON.parse(dataStr);
                if (parsed.type === "meta") {
                  if (this.onMeta) this.onMeta(parsed);
                } else if (parsed.type === "provider") {
                  if (this.onProvider) this.onProvider(parsed);
                } else if (parsed.type === "chunk") {
                  if (this.onChunk) this.onChunk(parsed.content);
                } else if (parsed.type === "error") {
                  if (this.onError) this.onError(new Error(parsed.content));
                } else if (parsed.type === "done") {
                  if (this.onDone) this.onDone();
                  return; // End the connection loop completely
                }
              } catch (err) {
                // Ignore parsing errors of incomplete chunks silently
              }
            }
          }
        }

        // If stream ended normally without [DONE], finish.
        if (this.onDone) this.onDone();
        return;
      } catch (error) {
        if (error.name === "AbortError") {
          this.hideToast();
          return;
        }

        if (error.message.includes("Permanent")) {
          this.hideToast();
          if (this.onError) this.onError(error);
          return;
        }

        // Transient error (Network down, 500 Server Error) - apply exponential backoff
        this.retryCount++;
        this.showToast();

        // Calculate backoff time: 2^retryCount * 1000ms (max 15 seconds)
        const backoffMs = Math.min(
          Math.pow(2, this.retryCount - 1) * 1000,
          15000,
        );

        // Wait before retrying (abortable)
        await new Promise((resolve) => {
          const timeoutId = setTimeout(resolve, backoffMs);
          this.abortController.signal.addEventListener("abort", () => {
            clearTimeout(timeoutId);
            resolve();
          });
        });

        // Loop continues to retry
      }
    }
  }

  abort() {
    this.abortController.abort();
    this.hideToast();
  }
}
