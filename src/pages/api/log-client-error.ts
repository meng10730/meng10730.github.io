import type { APIRoute } from "astro";
import fs from "fs-extra";
import path from "path";

export const prerender = false;

const LOG_DIR = path.resolve("logs");
const LOG_FILE = path.join(LOG_DIR, "client_error.log");
const MAX_LOG_SIZE = 2 * 1024 * 1024; // 2MB

export const POST: APIRoute = async ({ request }) => {
  // 僅限 localhost 存取
  const host = request.headers.get("host") || "";
  const isLocalhost = host.includes("localhost") || host.includes("127.0.0.1") || host.includes("[::1]") || host.startsWith("127.0.0.1:");
  
  if (!import.meta.env.DEV && !isLocalhost) {
    return new Response(
      JSON.stringify({ error: "此日誌 API 僅限本地開發環境 (localhost) 使用！" }),
      {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  try {
    const payload = await request.json();
    const { message, source, lineno, colno, stack } = payload;

    const timestamp = new Date().toISOString();
    let logLine = `[Client Error - ${timestamp}]
訊息: ${message || "無"}
來源: ${source || "無"}:${lineno || "無"}:${colno || "無"}
堆疊軌跡:
${stack || "無"}
----------------------------------------------------\n`;

    await fs.ensureDir(LOG_DIR);

    // 檢查檔案大小，防爆
    if (fs.existsSync(LOG_FILE)) {
      const stats = await fs.stat(LOG_FILE);
      if (stats.size > MAX_LOG_SIZE) {
        // 大於 2MB 則清空重寫
        await fs.writeFile(LOG_FILE, `[Log Cleared due to Size Limit at ${timestamp}]\n`, "utf-8");
      }
    }

    await fs.appendFile(LOG_FILE, logLine, "utf-8");

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};
