import { getToken } from "./api";

export function connectEvents(onMessage: (data: unknown) => void): WebSocket {
  const tok = getToken();
  const q = tok ? `?token=${encodeURIComponent(tok)}` : "";
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${window.location.host}/ws/events${q}`;
  const ws = new WebSocket(url);
  ws.onmessage = (ev) => {
    try {
      onMessage(JSON.parse(ev.data));
    } catch {
      onMessage({ type: "log", raw: ev.data });
    }
  };
  return ws;
}
