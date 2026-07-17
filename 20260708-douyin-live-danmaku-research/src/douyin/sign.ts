import type { HeaderMap, SignedWebcastConnection } from "./types.js";

interface SignServiceResponse {
  liveId?: string;
  roomId?: string;
  title?: string;
  wssUrl?: string;
  url?: string;
  headers?: HeaderMap;
  heartbeat?: {
    intervalMs?: number;
    payloadHex?: string;
  };
}

export interface SignRequest {
  liveId: string;
  cookie?: string;
  signUrl?: string;
  directWss?: string;
}

export async function getSignedConnection(request: SignRequest): Promise<SignedWebcastConnection> {
  if (request.directWss) {
    return {
      liveId: request.liveId,
      wssUrl: request.directWss,
      headers: buildHeaders(request.cookie),
    };
  }

  if (!request.signUrl) {
    throw new Error("缺少签名来源。传 --wss 已签名地址，或传 --sign-url 指向本地签名服务");
  }

  const response = await fetch(request.signUrl, {
    method: "POST",
    headers: {
      "content-type": "application/json",
    },
    body: JSON.stringify({
      liveId: request.liveId,
      cookie: request.cookie,
    }),
  });

  if (!response.ok) {
    throw new Error(`签名服务返回 ${response.status} ${response.statusText}`);
  }

  const body = (await response.json()) as SignServiceResponse;
  const wssUrl = body.wssUrl ?? body.url;
  if (!wssUrl || !wssUrl.startsWith("wss://")) {
    throw new Error("签名服务没有返回有效的 wssUrl");
  }

  return {
    liveId: body.liveId ?? request.liveId,
    roomId: body.roomId,
    title: body.title,
    wssUrl,
    headers: {
      ...buildHeaders(request.cookie),
      ...body.headers,
    },
    heartbeat: body.heartbeat,
  };
}

function buildHeaders(cookie?: string): HeaderMap {
  const headers: HeaderMap = {
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
  };

  if (cookie) {
    headers.cookie = cookie;
  }

  return headers;
}
