import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const TARGET_BASE_DIR = path.join(__dirname, "..", "src", "content");
const CONFIG_FILE = path.join(__dirname, "..", "sync-config.json");

// 動態載入 import-novels-cli.js 裡面的 PINYIN_MAP 與 S2T_DICT 對照表
let PINYIN_MAP = {};
let S2T_DICT = {};

try {
  const cliPath = path.join(__dirname, "import-novels-cli.js");
  if (fs.existsSync(cliPath)) {
    const cliCode = fs.readFileSync(cliPath, "utf-8");
    const pinyinMatch = cliCode.match(/const PINYIN_MAP = ({[\s\S]*?});/);
    const s2tMatch = cliCode.match(/const S2T_DICT = ({[\s\S]*?});/);
    if (pinyinMatch) {
      PINYIN_MAP = (new Function(`return ${pinyinMatch[1]}`))();
    }
    if (s2tMatch) {
      S2T_DICT = (new Function(`return ${s2tMatch[1]}`))();
    }
  }
} catch (e) {
  console.error("⚠️ 載入拼音或簡繁轉換對照表失敗，改用空白對照表:", e);
}

// 簡繁轉換
function convertToTraditional(text) {
  if (typeof text !== "string") return text;
  return text
    .split("")
    .map((char) => S2T_DICT[char] || char)
    .join("");
}

// 拼音網址別名
function pinyinSlugify(text) {
  if (!text) return "";
  const hasChinese = /[\u4e00-\u9fa5]/.test(text);
  if (!hasChinese) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)/g, "");
  }
  const chars = Array.from(text);
  const result = chars
    .map((char) => {
      if (/[a-zA-Z0-9]/.test(char)) return char.toLowerCase();
      if (PINYIN_MAP[char]) return PINYIN_MAP[char];
      return "";
    })
    .filter(Boolean)
    .join("-");
  return result.replace(/-+/g, "-").replace(/(^-|-$)/g, "");
}

// 建立全站標題對照表，用於雙括號連結解析
function buildTitleMap() {
  const titleMap = new Map();
  const collections = [
    "novels",
    "characters",
    "worldview",
    "factions",
    "guoxue",
    "items",
    "techniques",
    "bestiary",
    "blog"
  ];

  collections.forEach((col) => {
    const dir = path.join(TARGET_BASE_DIR, col);
    if (!fs.existsSync(dir)) return;

    try {
      const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md"));
      files.forEach((file) => {
        const filePath = path.join(dir, file);
        const raw = fs.readFileSync(filePath, "utf-8");
        const match = raw.match(/^---\n([\s\S]*?)\n---/);
        const slug = path.basename(file, ".md");

        if (match) {
          const lines = match[1].split("\n");
          let title = "";
          let aliasList = [];

          lines.forEach((line) => {
            if (line.startsWith("title:")) {
              title = line.replace("title:", "").replace(/["']/g, "").trim();
            } else if (line.startsWith("name:")) {
              title = line.replace("name:", "").replace(/["']/g, "").trim();
            } else if (line.startsWith("alias:")) {
              // 簡單陣列解析
              const val = line.replace("alias:", "").trim();
              if (val.startsWith("[") && val.endsWith("]")) {
                aliasList = val.slice(1, -1).split(",").map(a => a.replace(/["']/g, "").trim()).filter(Boolean);
              }
            }
          });

          if (title) {
            titleMap.set(title, { collection: col, slug });
          }
          aliasList.forEach((a) => {
            if (a) titleMap.set(a, { collection: col, slug });
          });
        }
      });
    } catch (e) {
      // 忽視單一目錄讀取失敗
    }
  });

  return titleMap;
}

// 格式標準化管道
function standardizeMarkdown(content, titleMap) {
  let clean = content
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .join("\n")
    .trim();

  // 雙括號連結轉為標準 Markdown 連結: [[厲絕鋒]] -> [厲絕鋒](/shanzhuang/characters/li-jue-feng)
  clean = clean.replace(
    /\[\[([^\]|#]+)(#[^\]|]+)?(?:\|([^\]]+))?\]\]/g,
    (match, baseTerm, anchor, aliasPart) => {
      const cleanBaseTerm = baseTerm.replace(/\.md$/i, "").trim();
      const cleanAnchor = anchor ? anchor.trim() : "";
      const aliasText = aliasPart ? aliasPart.replace(/^\|/, "").trim() : "";

      const matchInfo = titleMap.get(cleanBaseTerm);
      if (matchInfo) {
        const displayTitle = aliasText || cleanBaseTerm;
        // 將 blog 映射到部落格路徑，其餘映射到 shanzhuang 下
        const routePrefix = matchInfo.collection === "blog" ? "/blog" : `/shanzhuang/${matchInfo.collection}`;
        return `[${displayTitle}](${routePrefix}/${matchInfo.slug}${cleanAnchor})`;
      } else {
        return aliasText || cleanBaseTerm;
      }
    }
  );

  return clean;
}

// 將 JavaScript 物件轉換成 YAML 格式 Frontmatter
function toYAML(obj) {
  const lines = ["---"];
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined || value === null) continue;
    if (Array.isArray(value)) {
      lines.push(`${key}: [${value.map((v) => JSON.stringify(v)).join(", ")}]`);
    } else if (typeof value === "string") {
      // 如果包含冒號、換行等特殊字元，使用雙引號包含
      if (value.includes(":") || value.includes("\n") || value.includes(",") || value.includes("[") || value.includes("]")) {
        lines.push(`${key}: ${JSON.stringify(value)}`);
      } else {
        lines.push(`${key}: ${value}`);
      }
    } else {
      lines.push(`${key}: ${JSON.stringify(value)}`);
    }
  }
  lines.push("---");
  return lines.join("\n");
}

// 解析 Keystatic 設定檔生成 schema.json
function extractSchema() {
  const configPath = path.join(__dirname, "..", "keystatic.config.ts");
  if (!fs.existsSync(configPath)) {
    throw new Error(`找不到 Keystatic 設定檔: ${configPath}`);
  }
  
  const content = fs.readFileSync(configPath, "utf-8");
  const result = {};
  
  // 美化後的中文對照標籤
  const customLabels = {
    blog: "部落格文章 (blog，例如：閱讀心得、隨筆、日常)",
    novels: "小說連載 (novels，例如：小說正文)",
    characters: "人物設定 (characters，例如：人物誌)",
    worldview: "世界觀設定 (worldview，例如：小說設定、機制地理)",
    factions: "勢力組織 (factions)",
    guoxue: "國學筆記 (guoxue，例如：國學常識、經史子集)",
    items: "法寶神兵 (items)",
    techniques: "功法秘笈 (techniques)",
    bestiary: "靈獸妖魔 (bestiary)"
  };

  // 括號配對法擷取各個 collection 區塊
  let pos = content.indexOf("collections: {");
  if (pos === -1) {
    throw new Error("無法找到 collections 定義區塊");
  }
  pos += "collections: {".length;
  
  const regex = /(\w+):\s*collection\(\{/g;
  regex.lastIndex = pos;
  
  let match;
  while ((match = regex.exec(content)) !== null) {
    const name = match[1];
    if (name === "works") continue; // 排除不需從本機匯入的類型
    
    let start = regex.lastIndex;
    let braceCount = 1;
    let end = start;
    while (braceCount > 0 && end < content.length) {
      if (content[end] === '(') {
        braceCount++;
      } else if (content[end] === ')') {
        braceCount--;
      }
      end++;
    }
    
    const block = content.slice(start, end - 1);
    const labelMatch = block.match(/label:\s*["']([^"']+)["']/);
    const label = customLabels[name] || (labelMatch ? labelMatch[1] : name);
    
    // 用括號配對法取得 schema 區塊
    let schemaBlock = "";
    let schemaPos = block.indexOf("schema: {");
    if (schemaPos !== -1) {
      schemaPos += "schema: {".length;
      let sBraceCount = 1;
      let sEnd = schemaPos;
      while (sBraceCount > 0 && sEnd < block.length) {
        if (block[sEnd] === '{') {
          sBraceCount++;
        } else if (block[sEnd] === '}') {
          sBraceCount--;
        }
        sEnd++;
      }
      schemaBlock = block.slice(schemaPos, sEnd - 1);
    }
    
    const fields = {};
    if (schemaBlock) {
      const fieldRegex = /(\w+):\s*fields\.(\w+)\(/g;
      let fieldMatch;
      while ((fieldMatch = fieldRegex.exec(schemaBlock)) !== null) {
        const fieldName = fieldMatch[1];
        const fieldType = fieldMatch[2];
        if (fieldName === "content") continue; // 排除內文 content
        
        let fStart = fieldRegex.lastIndex;
        let fBraceCount = 1;
        let fEnd = fStart;
        while (fBraceCount > 0 && fEnd < schemaBlock.length) {
          if (schemaBlock[fEnd] === '(') {
            fBraceCount++;
          } else if (schemaBlock[fEnd] === ')') {
            fBraceCount--;
          }
          fEnd++;
        }
        const fieldArgs = schemaBlock.slice(fStart, fEnd - 1);
        
        let fieldLabel = fieldName;
        const flm = fieldArgs.match(/label:\s*["']([^"']+)["']/);
        if (flm) {
          fieldLabel = flm[1];
        } else {
          const flm2 = fieldArgs.match(/label:\s*["']([^"']+)["']/g);
          if (flm2 && flm2.length > 0) {
            const lastFlm = flm2[flm2.length - 1].match(/["']([^"']+)["']/);
            if (lastFlm) fieldLabel = lastFlm[1];
          }
        }
        
        const multiline = fieldArgs.includes("multiline: true");
        
        let options = [];
        if (fieldType === "select") {
          const optionsMatch = fieldArgs.match(/options:\s*\[([\s\S]*?)\]/);
          if (optionsMatch) {
            const optRegex = /\{\s*label:\s*["']([^"']+)["'],\s*value:\s*["']([^"']+)["']\s*\}/g;
            let optMatch;
            while ((optMatch = optRegex.exec(optionsMatch[1])) !== null) {
              options.push({ label: optMatch[1], value: optMatch[2] });
            }
          }
        }
        
        fields[fieldName] = {
          type: fieldType,
          label: fieldLabel,
          multiline: multiline,
          options: options.length > 0 ? options : undefined
        };
      }
    }
    
    result[name] = {
      label: label,
      fields: fields
    };
  }
  
  fs.writeFileSync(path.join(__dirname, "schema.json"), JSON.stringify(result, null, 2), "utf-8");
  console.log("✓ schema.json 提取成功！");
}


// 實行文檔標準化並寫入專案
function importDocument(filePath, collectionChoice, dataJSON) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`檔案不存在: ${filePath}`);
  }
  
  const rawContent = fs.readFileSync(filePath, "utf-8");
  
  // 解析 Markdown 的 Frontmatter
  let existingFrontmatter = {};
  let bodyContent = rawContent;
  
  const fmMatch = rawContent.match(/^---\n([\s\S]*?)\n---/);
  if (fmMatch) {
    bodyContent = rawContent.replace(fmMatch[0], "").trim();
    // 簡單的 YAML 鍵值解析
    fmMatch[1].split("\n").forEach((line) => {
      const colonIndex = line.indexOf(":");
      if (colonIndex > 0) {
        const key = line.slice(0, colonIndex).trim();
        let val = line.slice(colonIndex + 1).trim();
        if (val.startsWith("[") && val.endsWith("]")) {
          // 陣列
          existingFrontmatter[key] = val.slice(1, -1).split(",").map(v => v.replace(/["']/g, "").trim()).filter(Boolean);
        } else if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
          existingFrontmatter[key] = val.slice(1, -1);
        } else {
          existingFrontmatter[key] = val;
        }
      }
    });
  }
  
  // 覆寫或合併表單傳入的欄位資料
  const inputData = JSON.parse(dataJSON);
  const data = { ...existingFrontmatter, ...inputData };
  
  // 自動簡繁轉換 (僅轉換字串值，排除陣列等)
  for (const [key, value] of Object.entries(data)) {
    if (typeof value === "string") {
      data[key] = convertToTraditional(value);
    } else if (Array.isArray(value)) {
      data[key] = value.map((v) => (typeof v === "string" ? convertToTraditional(v) : v));
    }
  }
  
  // 網址別名 (Slugify)
  // characters 用 name, 其餘用 title
  const textForSlug = collectionChoice === "characters" ? data.name : data.title;
  if (!textForSlug) {
    throw new Error("欄位中缺失標題 (title) 或名稱 (name)，無法生成網頁別名 (Slug)！");
  }
  
  const cleanSlug = pinyinSlugify(textForSlug);
  
  // 執行 Wiki-links 解析標準化
  console.log("⌛ 正在建立標題對照表並解析雙括號連結...");
  const titleMap = buildTitleMap();
  const standardizedBody = standardizeMarkdown(bodyContent, titleMap);
  
  // 組合 YAML 與正文
  const finalFrontmatter = toYAML(data);
  const finalFileContent = `${finalFrontmatter}\n\n${standardizedBody}\n`;
  
  // 寫入檔案
  const targetDir = path.join(TARGET_BASE_DIR, collectionChoice);
  if (!fs.existsSync(targetDir)) {
    fs.mkdirSync(targetDir, { recursive: true });
  }
  
  const targetFilePath = path.join(targetDir, `${cleanSlug}.md`);
  fs.writeFileSync(targetFilePath, finalFileContent, "utf-8");
  
  // 更新 sync-config.json (如果它包含此檔案，或者將檔案記錄起來)
  // 如果 sync-config.json 設定了 novels，更新之
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const syncConfig = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf-8"));
      if (!syncConfig.novels) syncConfig.novels = {};
      
      const fileName = path.basename(filePath);
      syncConfig.novels[fileName] = {
        title: data.title || data.name,
        slug: cleanSlug,
        category: collectionChoice
      };
      fs.writeFileSync(CONFIG_FILE, JSON.stringify(syncConfig, null, 2), "utf-8");
    }
  } catch (e) {
    console.error("⚠️ 更新 sync-config.json 失敗:", e);
  }
  
  console.log(JSON.stringify({
    success: true,
    slug: cleanSlug,
    collection: collectionChoice,
    path: `src/content/${collectionChoice}/${cleanSlug}.md`
  }));
}

// 命令列接口調用
function main() {
  const args = process.argv.slice(2);
  if (args.includes("--extract")) {
    extractSchema();
  } else if (args.includes("--slugify")) {
    const textIndex = args.indexOf("--slugify") + 1;
    console.log(pinyinSlugify(args[textIndex]));
  } else if (args.includes("--convert")) {
    const textIndex = args.indexOf("--convert") + 1;
    console.log(convertToTraditional(args[textIndex]));
  } else if (args.includes("--import")) {
    const fileIdx = args.indexOf("--file") + 1;
    const colIdx = args.indexOf("--collection") + 1;
    const dataIdx = args.indexOf("--data") + 1;
    
    if (fileIdx > 0 && colIdx > 0 && dataIdx > 0) {
      importDocument(args[fileIdx], args[colIdx], args[dataIdx]);
    } else {
      console.error("❌ 缺失匯入參數！");
      process.exit(1);
    }
  } else {
    console.log("使用方式:");
    console.log("  node gui-helper.js --extract");
    console.log("  node gui-helper.js --slugify \"中文\"");
    console.log("  node gui-helper.js --convert \"简体字\"");
    console.log("  node gui-helper.js --import --file <路徑> --collection <分區> --data <JSON字串>");
  }
}

main();
