import { describe, it, expect, vi, afterEach } from 'vitest';
import { ChatConnection, mergeMessages, webSocketProtocols, type SocketLike, type TimelineMessage } from './chatTimeline';

const message = (id: number, key: string, seq = 0, version = 1): TimelineMessage => ({ id, client_message_id: key, seq, version, created_at: '2026-10-09T10:00:00Z' });

describe('message reconciliation', () => {
  it('keeps identical messages separate and replaces only the acknowledged command', () => {
    const result = mergeMessages([message(-1, 'a'), message(-2, 'b')], [message(10, 'b', 1)]);
    expect(result.map(m => m.id)).toEqual([10, -1]);
  });
  it('deduplicates HTTP and WS acknowledgements regardless of order', () => {
    const m = message(10, 'a', 1);
    expect(mergeMessages(mergeMessages([message(-1, 'a')], [m]), [m])).toEqual([m]);
  });
  it('does not restore deletions from delayed snapshots or old edits', () => {
    const deleted = new Map<number, number>();
    const result = mergeMessages([message(10, 'a', 1)], [{ ...message(10, 'a', 1, 2), is_deleted: true }], deleted);
    expect(mergeMessages(result, [message(10, 'a', 1)], deleted)).toEqual([]);
  });
  it('preserves newer edits and orders by server sequence', () => {
    const result = mergeMessages([message(20, 'b', 2, 3)], [message(20, 'b', 2), message(10, 'a', 1)]);
    expect(result.map(m => [m.id, m.version])).toEqual([[10, 1], [20, 3]]);
  });
  it('does not restore cleared history from a late acknowledgement or snapshot', () => {
    const result = mergeMessages([message(20, 'b', 2)], [message(10, 'a', 1), message(30, 'c', 3)], new Map(), 2);
    expect(result.map(m => m.id)).toEqual([30]);
  });
});

describe('connection lifecycle', () => {
  afterEach(() => vi.useRealTimers());
  it('passes bearer credentials through subprotocols without changing the URL', () => {
    const socket: SocketLike = {readyState:0,onopen:null,onmessage:null,onclose:null,onerror:null,close:vi.fn(),send:vi.fn()};
    const createSocket=vi.fn(()=>socket);
    const connection=new ChatConnection({url:()=> 'ws://test/ws/global/',protocols:()=>webSocketProtocols('test.jwt.value'),message:vi.fn(),state:vi.fn(),createSocket});
    connection.start();
    expect(createSocket).toHaveBeenCalledWith('ws://test/ws/global/',['animecore.v2','auth.test.jwt.value']);
    expect(webSocketProtocols('invalid token')).toEqual(['animecore.v2','auth.invalid']);
    connection.stop();
  });
  it('deduplicates CONNECTING and prevents old close events from reconnecting after stop', () => {
    vi.useFakeTimers();
    const sockets: SocketLike[] = [];
    const createSocket = vi.fn(() => {
      const socket: SocketLike = { readyState: 0, onopen: null, onmessage: null, onclose: null, onerror: null, close: vi.fn(), send: vi.fn() };
      sockets.push(socket);
      return socket;
    });
    const connection = new ChatConnection({ url: () => 'ws://test', message: vi.fn(), state: vi.fn(), createSocket });
    connection.start(); connection.start();
    expect(createSocket).toHaveBeenCalledTimes(1);
    const lateClose = sockets[0]!.onclose!;
    connection.stop(); connection.start();
    lateClose({ code: 1006 } as CloseEvent);
    vi.advanceTimersByTime(60000);
    expect(createSocket).toHaveBeenCalledTimes(2);
    connection.stop();
    expect(vi.getTimerCount()).toBe(0);
  });
});

it('includes visibility in global heartbeat frames without changing conversation pings', () => {
  vi.useFakeTimers();
  const socket: SocketLike={readyState:1,onopen:null,onmessage:null,onclose:null,onerror:null,send:vi.fn(),close:vi.fn()};
  const connection=new ChatConnection({url:()=> 'ws://test',message:vi.fn(),state:vi.fn(),createSocket:()=>socket,heartbeat:()=>({action:'ping',is_active:false})});
  connection.start(); socket.onopen!(new Event('open')); vi.advanceTimersByTime(25_000);
  expect(socket.send).toHaveBeenCalledWith(JSON.stringify({action:'ping',is_active:false})); connection.stop(); vi.useRealTimers();
});
