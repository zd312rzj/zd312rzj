import { EventEmitter } from "node:events";
import WebSocket from "ws";
import { createHeartbeatPayload, decodeWebcastFrame } from "./protocol.js";
import { getSignedConnection, type SignRequest } from "./sign.js";
import type { DouyinEvent, SignedWebcastConnection } from "./types.js";

export interface LiveClientOptions extends SignRequest {
  heartbeatIntervalMs?: number;
  reconnect?: boolean;
  maxReconnects?: number;
  showUnknown?: boolean;
}

export class DouyinLiveClient extends EventEmitter {
  private ws?: WebSocket;
  private stopped = false;
  private reconnectCount = 0;

  constructor(private readonly options: LiveClientOptions) {
    super();
  }

  async start(): Promise<void> {
    this.stopped = false;
    await this.connect();
  }

  stop(): void {
    this.stopped = true;
    this.ws?.close();
  }

  private async connect(): Promise<void> {
    const signed = await getSignedConnection(this.options);
    this.emit("system", systemEvent("connecting", `连接直播间 ${signed.roomId ?? signed.liveId ?? this.options.liveId}`));

    const ws = new WebSocket(signed.wssUrl, {
      headers: signed.headers,
      perMessageDeflate: false,
    });
    this.ws = ws;

    let heartbeatTimer: NodeJS.Timeout | undefined;

    ws.on("open", () => {
      this.reconnectCount = 0;
      this.emit("system", systemEvent("connected", "WebSocket已连接"));
      heartbeatTimer = this.startHeartbeat(ws, signed);
    });

    ws.on("message", (data) => {
      try {
        const decoded = decodeWebcastFrame(data);
        if (decoded.ack) {
          ws.send(decoded.ack);
        }

        for (const event of decoded.events) {
          if (event.type !== "unknown" || this.options.showUnknown) {
            this.emit("event", event);
          }
        }

        if (decoded.liveEnded) {
          this.stop();
        }
      } catch (error) {
        this.emit("system", systemEvent("decode_error", "消息解析失败", errorMessage(error)));
      }
    });

    ws.on("error", (error) => {
      this.emit("system", systemEvent("ws_error", "WebSocket出错", error.message));
    });

    ws.on("close", async (code, reason) => {
      if (heartbeatTimer) {
        clearInterval(heartbeatTimer);
      }

      this.emit("system", systemEvent("closed", `WebSocket已关闭，code=${code}`, reason.toString()));

      if (!this.stopped && this.options.reconnect !== false) {
        await this.reconnect();
      }
    });
  }

  private startHeartbeat(ws: WebSocket, signed: SignedWebcastConnection): NodeJS.Timeout {
    const payload = createHeartbeatPayload(signed.heartbeat?.payloadHex);
    const intervalMs =
      signed.heartbeat?.intervalMs ?? this.options.heartbeatIntervalMs ?? 5000;

    return setInterval(() => {
      if (ws.readyState !== WebSocket.OPEN) {
        return;
      }

      ws.ping(payload);
    }, intervalMs);
  }

  private async reconnect(): Promise<void> {
    const maxReconnects = this.options.maxReconnects ?? 5;
    if (this.reconnectCount >= maxReconnects) {
      this.emit("system", systemEvent("reconnect_give_up", "重连次数已用完"));
      return;
    }

    this.reconnectCount += 1;
    const delayMs = Math.min(30000, 1000 * 2 ** (this.reconnectCount - 1));
    this.emit("system", systemEvent("reconnecting", `${delayMs}ms后重连，第${this.reconnectCount}次`));

    await new Promise((resolve) => setTimeout(resolve, delayMs));
    if (!this.stopped) {
      await this.connect();
    }
  }
}

function systemEvent(event: string, message: string, detail?: unknown): DouyinEvent {
  return {
    type: "system",
    event,
    message,
    detail,
  };
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
