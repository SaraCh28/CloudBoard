/**
 * CloudBoard WebSocket Real-time Client (Module 8)
 * Manages WebSocket connection, auto-reconnection, typing indicators, and presence updates.
 */

class WebSocketClient {
  constructor() {
    this.ws = null;
    this.url = "ws://localhost:8005/ws/live";
    this.listeners = new Set();
    this.statusListeners = new Set();
    this.isConnected = false;
    this.reconnectTimer = null;
  }

  connect(userId = "user-1", userName = "Sara") {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsUrl = `${this.url}?user_id=${encodeURIComponent(userId)}&user_name=${encodeURIComponent(userName)}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnected = true;
      this.notifyStatus(true);
      console.log("⚡ WebSocket Connected to CloudBoard Live Cluster");
      
      // Start heartbeat
      this.pingInterval = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: "PING" }));
        }
      }, 25000);
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.notifyListeners(message);
      } catch (err) {
        console.error("Failed to parse WS message:", err);
      }
    };

    this.ws.onclose = () => {
      this.isConnected = false;
      this.notifyStatus(false);
      clearInterval(this.pingInterval);
      console.log("WebSocket Disconnected. Reconnecting in 5s...");
      this.reconnectTimer = setTimeout(() => this.connect(userId, userName), 5000);
    };

    this.ws.onerror = (err) => {
      console.warn("WebSocket error:", err);
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  onStatusChange(callback) {
    this.statusListeners.add(callback);
    return () => this.statusListeners.delete(callback);
  }

  notifyListeners(data) {
    this.listeners.forEach((listener) => listener(data));
  }

  notifyStatus(status) {
    this.statusListeners.forEach((listener) => listener(status));
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.ws) this.ws.close();
  }
}

export const wsClient = new WebSocketClient();
