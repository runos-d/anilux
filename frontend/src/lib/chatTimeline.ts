export interface TimelineMessage {
  id: number;
  client_message_id?: string | null;
  seq?: number;
  version?: number;
  created_at: string;
  is_deleted?: boolean;
  sender_id?: number;
  is_read_by_other?: boolean;
  read_count?: number;
}

/** The optimistic message and both HTTP/WS acknowledgements share one DOM node. */
export function messageRenderKey(message: TimelineMessage): string {
  return message.client_message_id && message.sender_id != null
    ? `command:${message.sender_id}:${message.client_message_id}`
    : `message:${message.id}`;
}

/** Reconcile server acknowledgements by command ID, never by text or time. */
export function mergeMessages<T extends TimelineMessage>(current: T[], incoming: T[], deleted = new Map<number, number>(), clearedThrough = 0): T[] {
  const visible = (m: T) => m.id < 0 || !m.seq || m.seq > clearedThrough;
  const records = new Map(current.filter(visible).map(m => [m.id, m]));
  for (const message of incoming) {
    if (!message.id) continue;
    const version = message.version ?? 1;
    if (message.is_deleted) {
      deleted.set(message.id, Math.max(deleted.get(message.id) ?? 0, version));
      records.delete(message.id);
      continue;
    }
    if (deleted.has(message.id)) continue;
    if (!visible(message)) continue;
    if (message.id > 0 && message.client_message_id) {
      for (const [id, pending] of records) {
        if (id < 0 && pending.client_message_id === message.client_message_id && pending.sender_id === message.sender_id) records.delete(id);
      }
    }
    const existing = records.get(message.id);
    if (existing && (existing.version ?? 1) > version) continue;
    records.set(message.id, { ...existing, ...message,
      ...(existing?.is_read_by_other ? { is_read_by_other: true } : {}),
      ...(existing?.read_count ? { read_count: Math.max(existing.read_count, message.read_count ?? 0) } : {}),
    });
  }
  return [...records.values()].sort((a, b) => {
    if (a.id < 0 || b.id < 0) {
      if (a.id < 0 && b.id > 0) return 1;
      if (b.id < 0 && a.id > 0) return -1;
    }
    return (a.seq ?? 0) - (b.seq ?? 0) || a.created_at.localeCompare(b.created_at) || a.id - b.id;
  });
}

export interface SocketLike {
  readyState: number;
  onopen: ((event: Event) => void) | null;
  onmessage: ((event: MessageEvent) => void) | null;
  onclose: ((event: CloseEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  send(data: string): void;
  close(): void;
}

export function webSocketProtocols(token: string): string[] {
  const protocols = ['animecore.v2'];
  if (token) protocols.push(`auth.${token.length <= 4096 && /^[A-Za-z0-9_.-]+$/.test(token) ? token : 'invalid'}`);
  return protocols;
}

/** Owns exactly one generation of a socket and cancels all retries on stop. */
export class ChatConnection {
  private socket: SocketLike | null = null;
  private retry: ReturnType<typeof setTimeout> | undefined;
  private heartbeat: ReturnType<typeof setInterval> | undefined;
  private attempts = 0;
  private generation = 0;
  private stopped = true;

  constructor(private options: {
    url: () => string;
    protocols?: () => string[];
    message: (data: Record<string, unknown>) => void;
    state: (connected: boolean) => void;
    opened?: () => void;
    heartbeat?: () => Record<string, unknown>;
    denied?: (code: number) => void;
    createSocket?: (url: string, protocols?: string[]) => SocketLike;
  }) {}

  start() {
    if (this.socket?.readyState === 0 || this.socket?.readyState === 1) return;
    this.stopped = false;
    const generation = ++this.generation;
    const socket = (this.options.createSocket ?? ((url, protocols) => new WebSocket(url, protocols)))(this.options.url(), this.options.protocols?.());
    this.socket = socket;
    const active = () => !this.stopped && generation === this.generation && this.socket === socket;
    socket.onopen = () => {
      if (!active()) return;
      this.attempts = 0;
      this.options.state(true);
      this.heartbeat = setInterval(() => this.send(this.options.heartbeat?.() ?? { action: 'ping' }), 25000);
      this.options.opened?.();
    };
    socket.onmessage = event => {
      if (!active()) return;
      try { this.options.message(JSON.parse(event.data)); } catch { /* invalid frame */ }
    };
    socket.onclose = event => {
      if (!active()) return;
      this.socket = null;
      clearInterval(this.heartbeat);
      this.options.state(false);
      if ([4001, 4003, 4004].includes(event.code)) {
        this.stopped = true;
        this.options.denied?.(event.code);
        return;
      }
      const ceiling = Math.min(30000, 1000 * 2 ** this.attempts++);
      this.retry = setTimeout(() => this.start(), 500 + Math.random() * (ceiling - 500));
    };
    socket.onerror = () => { /* close determines whether to retry */ };
  }

  send(data: unknown) {
    if (this.socket?.readyState === 1) this.socket.send(JSON.stringify(data));
  }

  stop() {
    this.stopped = true;
    ++this.generation;
    clearTimeout(this.retry);
    clearInterval(this.heartbeat);
    const socket = this.socket;
    this.socket = null;
    if (socket) {
      socket.onopen = socket.onmessage = socket.onclose = socket.onerror = null;
      socket.close();
    }
    this.options.state(false);
  }
}
