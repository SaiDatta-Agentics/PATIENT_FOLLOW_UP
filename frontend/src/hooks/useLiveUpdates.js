import { useEffect, useRef, useState } from 'react';

export default function useLiveUpdates(onEvent) {
  const [connected, setConnected] = useState(false);
  const callbackRef = useRef(onEvent);
  callbackRef.current = onEvent;

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/ws?token=${encodeURIComponent(token)}`;
    let ws;
    let retry;
    let heartbeat;
    let stopped = false;

    const connect = () => {
      if (stopped) return;
      ws = new WebSocket(url);
      ws.onopen = () => {
        setConnected(true);
        clearInterval(heartbeat);
        heartbeat = setInterval(() => {
          if (ws?.readyState === WebSocket.OPEN) ws.send('ping');
        }, 20000);
      };
      ws.onmessage = (event) => {
        try { callbackRef.current?.(JSON.parse(event.data)); } catch { /* ignore malformed event */ }
      };
      ws.onclose = () => {
        clearInterval(heartbeat);
        setConnected(false);
        if (!stopped) retry = setTimeout(connect, 2000);
      };
      ws.onerror = () => ws.close();
    };

    connect();
    return () => {
      stopped = true;
      clearTimeout(retry);
      clearInterval(heartbeat);
      if (ws && ws.readyState < 2) ws.close();
    };
  }, []);

  return connected;
}
