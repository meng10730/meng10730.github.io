import type { APIRoute } from "astro";
import fs from "fs-extra";
import path from "path";

export const prerender = false;

// 靜態預設值對照表 (Static Default Values Map)
const DEFAULT_VALUES: Record<string, Record<string, any>> = {
  blog: {
    title: "未命名部落格",
    description: "",
    pubDate: new Date(),
    tags: [],
  },
  works: {
    title: "未命名作品",
    description: "",
    category: "other",
    techs: [],
    status: "completed",
    pubDate: new Date(),
  },
  novels: {
    title: "未命名小說",
    description: "",
    genre: [],
    status: "ongoing",
    pubDate: new Date(),
  },
  characters: {
    name: "未命名角色",
    alias: [],
    tags: [],
    pubDate: new Date(),
  },
  worldview: {
    title: "未命名設定",
    category: "世界觀",
    pubDate: new Date(),
  },
  factions: {
    title: "未命名勢力",
    category: "正派",
    pubDate: new Date(),
  },
  guoxue: {
    title: "未命名國學筆記",
    category: "other",
    tags: [],
    pubDate: new Date(),
  },
  items: {
    title: "未命名法寶",
    pubDate: new Date(),
  },
  techniques: {
    title: "未命名功法",
    pubDate: new Date(),
  },
  bestiary: {
    title: "未命名靈獸",
    pubDate: new Date(),
  },
};

// 每個集合合法的 Frontmatter 欄位
const VALID_FIELDS: Record<string, string[]> = {
  blog: ["title", "description", "pubDate", "tags"],
  works: ["title", "description", "category", "techs", "status", "github", "demo", "pubDate"],
  novels: ["title", "description", "genre", "status", "pubDate", "cover"],
  characters: ["name", "description", "alias", "affiliation", "novel", "tags", "pubDate"],
  worldview: ["title", "description", "category", "pubDate"],
  factions: ["title", "description", "category", "pubDate"],
  guoxue: ["title", "source", "category", "tags", "pubDate"],
  items: ["title", "description", "novel", "rank", "pubDate"],
  techniques: ["title", "description", "novel", "type", "pubDate"],
  bestiary: ["title", "description", "novel", "pubDate"],
};

// 解析 Markdown
function parseMarkdown(content: string) {
  const lines = content.split(/\r?\n/);
  if (lines[0] !== '---') {
    return { frontmatter: {} as Record<string, any>, body: content, hasFrontmatter: false };
  }
  
  let endIdx = -1;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i] === '---') {
      endIdx = i;
      break;
    }
  }
  
  if (endIdx === -1) {
    return { frontmatter: {} as Record<string, any>, body: content, hasFrontmatter: false };
  }
  
  const frontmatterLines = lines.slice(1, endIdx);
  const body = lines.slice(endIdx + 1).join('\n');
  
  const frontmatter: Record<string, any> = {};
  let currentKey: string | null = null;
  
  for (const line of frontmatterLines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    
    // 檢查是否是 list 項，例如 "- tag1"
    if (trimmed.startsWith('-') && currentKey) {
      let val = trimmed.slice(1).trim();
      // 去除首尾引號
      val = val.replace(/^['"]|['"]$/g, '');
      if (Array.isArray(frontmatter[currentKey])) {
        frontmatter[currentKey].push(val);
      } else {
        frontmatter[currentKey] = [val];
      }
      continue;
    }
    
    const colonIdx = line.indexOf(':');
    if (colonIdx !== -1) {
      const key = line.slice(0, colonIdx).trim();
      const valStr = line.slice(colonIdx + 1).trim();
      currentKey = key;
      
      if (valStr === '') {
        frontmatter[key] = [];
      } else {
        let val: any = valStr.replace(/^['"]|['"]$/g, '');
        if (val === 'true') val = true;
        else if (val === 'false') val = false;
        else if (!isNaN(Number(val)) && val !== '') val = Number(val);
        frontmatter[key] = val;
      }
    }
  }
  
  return { frontmatter, body, hasFrontmatter: true };
}

// 格式化為 YAML Frontmatter
function stringifyFrontmatter(frontmatter: Record<string, any>): string {
  let yaml = '---\n';
  for (const [key, val] of Object.entries(frontmatter)) {
    if (val === undefined || val === null) continue;
    if (Array.isArray(val)) {
      yaml += `${key}:\n`;
      for (const item of val) {
        yaml += `  - ${JSON.stringify(item)}\n`;
      }
    } else if (typeof val === 'object' && val instanceof Date) {
      const yyyy = val.getFullYear();
      const mm = String(val.getMonth() + 1).padStart(2, '0');
      const dd = String(val.getDate()).padStart(2, '0');
      yaml += `${key}: ${yyyy}-${mm}-${dd}\n`;
    } else if (typeof val === 'string') {
      if (/^\d{4}-\d{2}-\d{2}/.test(val)) {
        yaml += `${key}: ${val.split('T')[0]}\n`;
      } else {
        yaml += `${key}: ${JSON.stringify(val)}\n`;
      }
    } else {
      yaml += `${key}: ${val}\n`;
    }
  }
  yaml += '---';
  return yaml;
}

// 解析 HTML 註解備份欄位
function parseBackupFields(body: string) {
  const backupRegex = /<!--\s*KEYSTATIC_BACKUP_FIELDS\s*\r?\n([\s\S]*?)\r?\n\s*-->/;
  const match = body.match(backupRegex);
  
  const backupFields: Record<string, any> = {};
  let cleanBody = body;
  
  if (match) {
    const yamlLikeContent = match[1];
    cleanBody = body.replace(backupRegex, '').trim();
    
    const lines = yamlLikeContent.split(/\r?\n/);
    let currentKey: string | null = null;
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      if (trimmed.startsWith('-') && currentKey) {
        let val = trimmed.slice(1).trim();
        val = val.replace(/^['"]|['"]$/g, '');
        if (Array.isArray(backupFields[currentKey])) {
          backupFields[currentKey].push(val);
        } else {
          backupFields[currentKey] = [val];
        }
        continue;
      }
      
      const colonIdx = line.indexOf(':');
      if (colonIdx !== -1) {
        const key = line.slice(0, colonIdx).trim();
        const valStr = line.slice(colonIdx + 1).trim();
        currentKey = key;
        
        if (valStr === '') {
          backupFields[key] = [];
        } else {
          let val: any = valStr.replace(/^['"]|['"]$/g, '');
          if (val === 'true') val = true;
          else if (val === 'false') val = false;
          else if (val.startsWith('[') && val.endsWith(']')) {
            try {
              val = JSON.parse(val);
            } catch {
              // fallback
            }
          } else if (!isNaN(Number(val)) && val !== '') {
            val = Number(val);
          }
          backupFields[key] = val;
        }
      }
    }
  }
  
  return { backupFields, cleanBody };
}

// 格式化 HTML 註解備份欄位
function stringifyBackupFields(fields: Record<string, any>): string {
  const entries = Object.entries(fields);
  if (entries.length === 0) return '';
  
  let result = '<!-- KEYSTATIC_BACKUP_FIELDS\n';
  for (const [key, val] of entries) {
    if (val === undefined || val === null) continue;
    if (Array.isArray(val)) {
      result += `${key}:\n`;
      for (const item of val) {
        result += `  - ${JSON.stringify(item)}\n`;
      }
    } else {
      result += `${key}: ${JSON.stringify(val)}\n`;
    }
  }
  result += '-->';
  return result;
}

export const POST: APIRoute = async ({ request }) => {
  // 1. 線上環境阻擋 (Production 封印 - 允許 localhost 存取)
  const host = request.headers.get("host") || "";
  const isLocalhost = host.includes("localhost") || host.includes("127.0.0.1") || host.includes("[::1]") || host.startsWith("127.0.0.1:");
  
  if (!import.meta.env.DEV && !isLocalhost) {
    return new Response(
      JSON.stringify({ error: "此移置閣 API 僅限本地開發環境 (localhost) 使用！" }),
      {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  try {
    const bodyText = await request.text();
    let payload;
    try {
      payload = JSON.parse(bodyText);
    } catch {
      return new Response(JSON.stringify({ error: "無法解析 JSON Payload" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const { changes } = payload;
    if (!Array.isArray(changes)) {
      return new Response(JSON.stringify({ error: "參數 changes 必須為陣列" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const results: Array<{ slug: string; from: string; to: string; success: boolean; error?: string }> = [];

    // 開始逐一處理移置
    for (const change of changes) {
      const { slug, fromCollection, toCollection, newCategory } = change;

      if (!slug || !fromCollection || !toCollection) {
        results.push({ slug, from: fromCollection, to: toCollection, success: false, error: "缺少必要欄位" });
        continue;
      }

      const fromDir = path.resolve("src/content", fromCollection);
      const toDir = path.resolve("src/content", toCollection);
      
      const fromPath = path.join(fromDir, `${slug}.md`);
      const toPath = path.join(toDir, `${slug}.md`);

      // 檢查來源檔案是否存在
      if (!fs.existsSync(fromPath)) {
        results.push({ slug, from: fromCollection, to: toCollection, success: false, error: `來源檔案不存在: ${fromPath}` });
        continue;
      }

      // 2. 防碰撞檢查（目標若有同名檔案則嚴格阻擋並報錯）
      if (fs.existsSync(toPath)) {
        return new Response(
          JSON.stringify({ error: `目標集合已存在同名檔案: "${slug}.md"` }),
          {
            status: 409,
            headers: { "Content-Type": "application/json" },
          }
        );
      }

      // 3. 備份原檔案至根目錄下的 .backup/
      const backupDir = path.resolve(".backup", fromCollection);
      await fs.ensureDir(backupDir);
      const backupPath = path.join(backupDir, `${slug}.md`);
      await fs.copy(fromPath, backupPath);

      // 4. 讀取並解析
      const rawContent = await fs.readFile(fromPath, "utf-8");
      const { frontmatter, body } = parseMarkdown(rawContent);
      const { backupFields: oldBackupFields, cleanBody } = parseBackupFields(body);

      // 5. 進行欄位對齊與預設值填充
      const newFrontmatter: Record<string, any> = {};
      const newBackupFields: Record<string, any> = { ...oldBackupFields };

      // 對等欄位轉換：name <-> title
      if (toCollection === "characters") {
        if (!frontmatter.name && frontmatter.title) {
          frontmatter.name = frontmatter.title;
        }
      } else {
        if (!frontmatter.title && frontmatter.name) {
          frontmatter.title = frontmatter.name;
        }
      }

      // 取得目標集合的合法欄位
      const targetValidFields = VALID_FIELDS[toCollection] || [];
      
      // 將來源 frontmatter 的欄位分類到新 frontmatter 或備份中
      for (const [key, value] of Object.entries(frontmatter)) {
        if (targetValidFields.includes(key)) {
          newFrontmatter[key] = value;
        } else {
          // 不相容特有欄位，移入備份註解
          newBackupFields[key] = value;
        }
      }

      // 如果目標集合有 category 欄位，且傳入了 newCategory
      if (targetValidFields.includes("category")) {
        if (newCategory) {
          newFrontmatter.category = newCategory;
        } else if (!newFrontmatter.category) {
          newFrontmatter.category = DEFAULT_VALUES[toCollection]?.category || "未分類";
        }
      }

      // 填充目標集合的必填/預設值
      const defaultMap = DEFAULT_VALUES[toCollection] || {};
      for (const key of targetValidFields) {
        if (newFrontmatter[key] === undefined) {
          const val = defaultMap[key];
          if (val instanceof Date) {
            newFrontmatter[key] = val.toISOString().split("T")[0];
          } else {
            newFrontmatter[key] = val;
          }
        }
      }

      // 6. Markdown 內文相對圖片路徑自動層級修正
      const markdownImageRegex = /(!\[.*?\]\()((?:\.|\.\.)\/[^\)]+)(\))/g;
      const htmlImageRegex = /(<img\s+[^>]*src=["'])((?:\.|\.\.)\/[^"']+)(["'])/g;

      let updatedBody = cleanBody;

      updatedBody = updatedBody.replace(markdownImageRegex, (match, prefix, relPath, suffix) => {
        const absImgPath = path.resolve(fromDir, relPath);
        let newRelPath = path.relative(toDir, absImgPath);
        newRelPath = newRelPath.replace(/\\/g, "/");
        if (!newRelPath.startsWith(".")) {
          newRelPath = "./" + newRelPath;
        }
        return `${prefix}${newRelPath}${suffix}`;
      });

      updatedBody = updatedBody.replace(htmlImageRegex, (match, prefix, relPath, suffix) => {
        const absImgPath = path.resolve(fromDir, relPath);
        let newRelPath = path.relative(toDir, absImgPath);
        newRelPath = newRelPath.replace(/\\/g, "/");
        if (!newRelPath.startsWith(".")) {
          newRelPath = "./" + newRelPath;
        }
        return `${prefix}${newRelPath}${suffix}`;
      });

      // 7. 組合新檔案內容
      const newFrontmatterStr = stringifyFrontmatter(newFrontmatter);
      const newBackupFieldsStr = stringifyBackupFields(newBackupFields);
      
      const finalMarkdownContent = `${newFrontmatterStr}\n${
        newBackupFieldsStr ? newBackupFieldsStr + "\n\n" : ""
      }${updatedBody}`;

      // 8. 物理寫入目標路徑與刪除舊檔
      await fs.ensureDir(toDir);
      await fs.writeFile(toPath, finalMarkdownContent, "utf-8");
      await fs.remove(fromPath);

      results.push({ slug, from: fromCollection, to: toCollection, success: true });
    }

    // 檢查是否有全部失敗的情況
    const anySuccess = results.some((r) => r.success);
    if (!anySuccess && results.length > 0) {
      return new Response(
        JSON.stringify({ error: "所有檔案搬移均失敗", details: results }),
        {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    return new Response(JSON.stringify({ success: true, details: results }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message || "伺服器內部錯誤" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
};
