import protobuf from "protobufjs";
import { gunzipSync } from "node:zlib";
import type { ChatEvent, DouyinEvent, UnknownMessageEvent } from "./types.js";

const PROTO = `
syntax = "proto3";

message PushFrame {
  uint64 seqId = 1;
  uint64 logId = 2;
  uint64 service = 3;
  uint64 method = 4;
  repeated HeadersList headersList = 5;
  string payloadEncoding = 6;
  string payloadType = 7;
  bytes payload = 8;
}

message HeadersList {
  string key = 1;
  string value = 2;
}

message Response {
  repeated Message messagesList = 1;
  string cursor = 2;
  uint64 fetchInterval = 3;
  uint64 now = 4;
  string internalExt = 5;
  uint32 fetchType = 6;
  uint64 heartbeatDuration = 8;
  bool needAck = 9;
  string pushServer = 10;
  string liveCursor = 11;
  bool historyNoMore = 12;
}

message Message {
  string method = 1;
  bytes payload = 2;
  int64 msgId = 3;
  int32 msgType = 4;
  int64 offset = 5;
  bool needWrdsStore = 6;
  int64 wrdsVersion = 7;
  string wrdsSubKey = 8;
}

message ChatMessage {
  Common common = 1;
  User user = 2;
  string content = 3;
  uint64 eventTime = 15;
}

message EmojiChatMessage {
  Common common = 1;
  User user = 2;
  int64 emojiId = 3;
  string defaultContent = 5;
}

message ControlMessage {
  Common common = 1;
  int32 status = 2;
}

message Common {
  string method = 1;
  uint64 msgId = 2;
  uint64 roomId = 3;
  uint64 createTime = 4;
}

message User {
  uint64 id = 1;
  uint64 shortId = 2;
  string nickName = 3;
  string displayId = 38;
  string secUid = 46;
  string idStr = 1028;
}
`;

const root = protobuf.parse(PROTO).root;
const PushFrame = root.lookupType("PushFrame");
const Response = root.lookupType("Response");
const ChatMessage = root.lookupType("ChatMessage");
const EmojiChatMessage = root.lookupType("EmojiChatMessage");
const ControlMessage = root.lookupType("ControlMessage");

export interface DecodedFrame {
  frame: protobuf.Message<Record<string, unknown>>;
  response: protobuf.Message<Record<string, unknown>>;
  events: DouyinEvent[];
  ack?: Uint8Array;
  liveEnded: boolean;
}

export function createHeartbeatPayload(hex?: string): Uint8Array {
  if (hex) {
    return Buffer.from(hex, "hex");
  }

  return PushFrame.encode(PushFrame.create({ payloadType: "hb" })).finish();
}

export function decodeWebcastFrame(input: Buffer | ArrayBuffer | Buffer[]): DecodedFrame {
  const data = Buffer.isBuffer(input)
    ? input
    : Array.isArray(input)
      ? Buffer.concat(input)
      : Buffer.from(input);

  const frame = PushFrame.decode(data);
  const frameObject = PushFrame.toObject(frame, { longs: String, bytes: Buffer });
  const payload = getBytes(frameObject.payload);
  const responsePayload = frameObject.payloadEncoding === "gzip" ? gunzipSync(payload) : payload;
  const response = Response.decode(responsePayload);
  const responseObject = Response.toObject(response, { longs: String, bytes: Buffer }) as {
    messagesList?: Array<{ method?: string; payload?: Buffer; msgId?: string }>;
    needAck?: boolean;
    internalExt?: string;
  };

  const events: DouyinEvent[] = [];
  let liveEnded = false;

  for (const message of responseObject.messagesList ?? []) {
    const method = message.method ?? "unknown";
    if (method === "WebcastChatMessage") {
      events.push(parseChat(message.payload, method));
      continue;
    }

    if (method === "WebcastEmojiChatMessage") {
      events.push(parseEmojiChat(message.payload, method));
      continue;
    }

    if (method === "WebcastControlMessage") {
      const control = ControlMessage.toObject(ControlMessage.decode(getBytes(message.payload)), { longs: String }) as {
        status?: number;
      };
      if (control.status === 3) {
        liveEnded = true;
        events.push({
          type: "system",
          event: "live_ended",
          message: "直播间已结束",
        });
      }
      continue;
    }

    const unknown: UnknownMessageEvent = {
      type: "unknown",
      method,
      msg_id: message.msgId,
    };
    events.push(unknown);
  }

  const ack =
    responseObject.needAck === true
      ? PushFrame.encode(
          PushFrame.create({
            logId: frameObject.logId,
            payloadType: "ack",
            payload: Buffer.from(responseObject.internalExt ?? "", "utf8"),
          }),
        ).finish()
      : undefined;

  return {
    frame,
    response,
    events,
    ack,
    liveEnded,
  };
}

function parseChat(payload: Buffer | undefined, method: string): ChatEvent {
  const decoded = ChatMessage.decode(getBytes(payload));
  const object = ChatMessage.toObject(decoded, { longs: String }) as {
    common?: { roomId?: string; createTime?: string };
    user?: { id?: string; idStr?: string; nickName?: string };
    content?: string;
    eventTime?: string;
  };

  return {
    type: "chat",
    room_id: object.common?.roomId,
    user_id: object.user?.idStr ?? object.user?.id,
    nickname: object.user?.nickName,
    content: object.content ?? "",
    timestamp: toNumber(object.eventTime ?? object.common?.createTime),
    method,
  };
}

function parseEmojiChat(payload: Buffer | undefined, method: string): ChatEvent {
  const decoded = EmojiChatMessage.decode(getBytes(payload));
  const object = EmojiChatMessage.toObject(decoded, { longs: String }) as {
    common?: { roomId?: string; createTime?: string };
    user?: { id?: string; idStr?: string; nickName?: string };
    defaultContent?: string;
  };

  return {
    type: "chat",
    room_id: object.common?.roomId,
    user_id: object.user?.idStr ?? object.user?.id,
    nickname: object.user?.nickName,
    content: object.defaultContent ?? "[emoji]",
    timestamp: toNumber(object.common?.createTime),
    method,
  };
}

function getBytes(value: unknown): Buffer {
  if (!value) {
    return Buffer.alloc(0);
  }

  if (Buffer.isBuffer(value)) {
    return value;
  }

  if (value instanceof Uint8Array) {
    return Buffer.from(value);
  }

  throw new Error("protobuf payload 不是二进制数据");
}

function toNumber(value: string | undefined): number | undefined {
  if (!value) {
    return undefined;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}
