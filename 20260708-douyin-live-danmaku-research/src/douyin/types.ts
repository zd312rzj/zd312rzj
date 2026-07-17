export type HeaderMap = Record<string, string>;

export interface SignedWebcastConnection {
  liveId?: string;
  roomId?: string;
  title?: string;
  wssUrl: string;
  headers?: HeaderMap;
  heartbeat?: {
    intervalMs?: number;
    payloadHex?: string;
  };
}

export interface ChatEvent {
  type: "chat";
  room_id?: string;
  user_id?: string;
  nickname?: string;
  content: string;
  timestamp?: number;
  method: string;
}

export interface SystemEvent {
  type: "system";
  event: string;
  message: string;
  detail?: unknown;
}

export interface UnknownMessageEvent {
  type: "unknown";
  method: string;
  msg_id?: string;
}

export type DouyinEvent = ChatEvent | SystemEvent | UnknownMessageEvent;
