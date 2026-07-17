export function parseLiveId(input: string): string {
  const trimmed = input.trim();
  if (!trimmed) {
    throw new Error("直播间地址或房间号为空");
  }

  if (/^\d+$/.test(trimmed)) {
    return trimmed;
  }

  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    throw new Error("无法识别直播间地址，请传入 https://live.douyin.com/xxxx 或纯数字房间号");
  }

  const parts = url.pathname.split("/").filter(Boolean);
  const candidate = parts.at(-1);
  if (!candidate || !/^[A-Za-z0-9_-]+$/.test(candidate)) {
    throw new Error("直播间地址里没有找到有效房间标识");
  }

  return candidate;
}
