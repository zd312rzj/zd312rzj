import { Command } from "commander";
import { DouyinLiveClient } from "./douyin/client.js";
import { parseLiveId } from "./douyin/room.js";
import type { DouyinEvent } from "./douyin/types.js";

const program = new Command();

program
  .name("douyin-live-danmaku")
  .description("抖音直播弹幕非官方路线本地PoC")
  .option("-l, --live <urlOrId>", "直播间URL或房间标识")
  .option("--wss <url>", "已签名的WebSocket地址")
  .option("--sign-url <url>", "本地签名服务地址，例如 http://127.0.0.1:8787/sign")
  .option("--cookie <cookie>", "可选Cookie，只从命令行传入，不写入文件")
  .option("--unknown", "打印未知消息类型")
  .option("--no-reconnect", "关闭自动重连")
  .option("--max-reconnects <count>", "最大重连次数", "5")
  .option("--heartbeat <ms>", "心跳间隔毫秒", "5000")
  .parse();

const options = program.opts<{
  live?: string;
  wss?: string;
  signUrl?: string;
  cookie?: string;
  unknown?: boolean;
  reconnect?: boolean;
  maxReconnects: string;
  heartbeat: string;
}>();

async function main(): Promise<void> {
  const liveId = parseLiveId(options.live ?? extractLiveIdFromWss(options.wss) ?? "");
  const client = new DouyinLiveClient({
    liveId,
    directWss: options.wss,
    signUrl: options.signUrl,
    cookie: options.cookie,
    showUnknown: options.unknown,
    reconnect: options.reconnect,
    maxReconnects: Number.parseInt(options.maxReconnects, 10),
    heartbeatIntervalMs: Number.parseInt(options.heartbeat, 10),
  });

  client.on("system", printEvent);
  client.on("event", printEvent);

  process.on("SIGINT", () => {
    printEvent({ type: "system", event: "stopping", message: "收到停止信号" });
    client.stop();
  });

  await client.start();
}

function printEvent(event: DouyinEvent): void {
  process.stdout.write(`${JSON.stringify(event, null, 0)}\n`);
}

function extractLiveIdFromWss(wss: string | undefined): string | undefined {
  if (!wss) {
    return undefined;
  }

  try {
    const url = new URL(wss);
    return url.searchParams.get("room_id") ?? undefined;
  } catch {
    return undefined;
  }
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${JSON.stringify({ type: "system", event: "fatal", message })}\n`);
  process.exitCode = 1;
});
