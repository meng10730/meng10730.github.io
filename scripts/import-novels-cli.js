import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import readline from "readline";
import { execSync } from "child_process";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const CONFIG_FILE = path.join(__dirname, "..", "sync-config.json");
const TARGET_BASE_DIR = path.join(__dirname, "..", "src", "content");

// 常用小說與設定集漢字拼音對照表，供自動 Slugify 使用
const PINYIN_MAP = {
  不: "bu",
  夜: "ye",
  侯: "hou",
  厲: "li",
  絕: "jue",
  鋒: "feng",
  司: "si",
  南: "nan",
  塵: "chen",
  燼: "jin",
  蠲: "juan",
  歲: "sui",
  戲: "xi",
  長: "chang",
  安: "an",
  摘: "zhai",
  雲: "yun",
  斬: "zhan",
  荒: "huang",
  飲: "yin",
  劫: "jie",
  晏: "yan",
  雪: "xue",
  楚: "chu",
  韶: "shao",
  華: "hua",
  樓: "lou",
  深: "shen",
  闕: "que",
  歧: "qi",
  歿: "mo",
  古: "gu",
  江: "jiang",
  無: "wu",
  岸: "an",
  澹: "dan",
  臺: "tai",
  翣: "sha",
  煙: "yan",
  蘿: "luo",
  白: "bai",
  檀: "tan",
  百: "bai",
  年: "nian",
  裁: "cai",
  罰: "fa",
  者: "zhe",
  研: "yan",
  辭: "ci",
  蒹: "jian",
  葭: "jia",
  蘇: "su",
  挽: "wan",
  風: "feng",
  陸: "lu",
  涯: "ya",
  雙: "shuang",
  魂: "hun",
  皇: "huang",
  帝: "di",
  九: "jiu",
  宮: "gong",
  格: "ge",
  乾: "qian",
  坤: "kun",
  秩: "zhi",
  序: "xu",
  矩: "ju",
  陣: "zhen",
  天: "tian",
  羃: "mi",
  遺: "yi",
  玉: "yu",
  六: "liu",
  器: "qi",
  本: "ben",
  源: "yuan",
  服: "fu",
  飾: "shi",
  性: "xing",
  表: "biao",
  象: "xiang",
  日: "ri",
  常: "chang",
  習: "xi",
  慣: "guan",
  瞳: "tong",
  孔: "kong",
  神: "shen",
  態: "tai",
  種: "zhong",
  族: "zu",
  血: "xue",
  統: "tong",
  膚: "fu",
  色: "se",
  外: "wai",
  貌: "mao",
  頭: "tou",
  髮: "fa",
  型: "xing",
  特: "te",
  殊: "shu",
  能: "neng",
  力: "li",
  全: "quan",
  維: "wei",
  徵: "zheng",
  美: "mei",
  學: "xue",
  總: "zong",
  綱: "gang",
  舊: "jiu",
  世: "shi",
  中: "zhong",
  陰: "yin",
  界: "jie",
  角: "jiao",
  設: "she",
  草: "cao",
  案: "an",
  擴: "kuo",
  chong: "chong",
  組: "zu",
  織: "zhi",
  正: "zheng",
  派: "pai",
  提: "ti",
  浮: "fu",
  生: "sheng",
  極: "ji",
  樂: "le",
  坊: "fang",
  定: "ding",
  碑: "bei",
  內: "nei",
  部: "bu",
  構: "gou",
  造: "zao",
  級: "ji",
  勢: "shi",
  質: "zhi",
  詞: "ci",
  條: "tiao",
  庫: "ku",
  觀: "guan",
  星: "xing",
  閣: "ge",
};

// 簡體到繁體字典 (常用於小說設定與標題欄位)
const S2T_DICT = {
  体: "體",
  国: "國",
  华: "華",
  诀: "訣",
  剑: "劍",
  门: "門",
  庄: "莊",
  阁: "閣",
  势: "勢",
  织: "織",
  组: "組",
  头: "頭",
  发: "髮",
  无: "無",
  双: "雙",
  皇: "皇",
  帝: "帝",
  炼: "煉",
  炉: "爐",
  经: "經",
  记: "記",
  录: "錄",
  传: "傳",
  侠: "俠",
  义: "義",
  导: "導",
  选: "選",
  择: "擇",
  标: "標",
  准: "準",
  确: "確",
  实: "實",
  现: "現",
  动: "動",
  态: "態",
  备: "備",
  测: "測",
  试: "試",
  验: "驗",
  证: "證",
  规: "規",
  则: "則",
  检: "檢",
  查: "查",
  校: "校",
  对: "對",
  转: "轉",
  换: "換",
  简: "簡",
  繁: "繁",
  单: "單",
  向: "向",
  同: "同",
  步: "步",
  警: "警",
  防: "防",
  类: "類",
  别: "別",
  路: "路",
  由: "由",
  配: "配",
  置: "置",
  表: "表",
  后: "後",
  台: "台",
  注: "註",
  册: "冊",
  排: "排",
  版: "版",
  修: "修",
  改: "改",
  前: "前",
  写: "寫",
  入: "入",
  与: "與",
  万: "萬",
  术: "術",
  兽: "獸",
  魔: "魔",
  灵: "靈",
  宝: "寶",
  说: "說",
  书: "書",
  战: "戰",
  斗: "鬥",
  气: "氣",
  啸: "嘯",
  风: "風",
  云: "雲",
  雷: "雷",
  电: "電",
  斩: "斬",
  杀: "殺",
  灭: "滅",
  绝: "絕",
  隐: "隱",
  现: "現",
  迹: "跡",
  踪: "蹤",
  寻: "尋",
  觅: "覓",
  见: "見",
  觉: "覺",
  览: "覽",
  读: "讀",
  听: "聽",
  谈: "談",
  议: "議",
  论: "論",
  评: "評",
  识: "識",
  话: "話",
  诉: "訴",
  该: "該",
  详: "詳",
  诸: "諸",
  诺: "諾",
  谁: "誰",
  调: "調",
  谅: "諒",
  谈: "談",
  谊: "誼",
  谋: "謀",
  谍: "諜",
  谎: "謊",
  谐: "諧",
  谜: "謎",
  谦: "謙",
  谨: "謹",
  谬: "謬",
  谱: "譜",
  贝: "貝",
  贞: "貞",
  负: "負",
  贡: "貢",
  财: "財",
  责: "責",
  贤: "賢",
  败: "敗",
  账: "帳",
  货: "貨",
  质: "質",
  贩: "販",
  贪: "貪",
  贫: "貧",
  贬: "貶",
  购: "購",
  贮: "貯",
  贯: "貫",
  贴: "貼",
  贵: "貴",
  贷: "貸",
  贸: "貿",
  费: "費",
  贺: "賀",
  贻: "貽",
  贼: "賊",
  贾: "賈",
  贿: "賄",
  资: "資",
  赔: "賠",
  赖: "賴",
  赘: "贅",
  赚: "賺",
  赛: "賽",
  赞: "贊",
  赠: "贈",
  赢: "贏",
  车: "車",
  轨: "軌",
  轩: "軒",
  轮: "輪",
  软: "軟",
  轰: "轟",
  轴: "軸",
  轻: "輕",
  载: "載",
  较: "較",
  辅: "輔",
  辆: "輛",
  辈: "輩",
  辉: "輝",
  辑: "輯",
  输: "輸",
  辖: "轄",
  辗: "輾",
  辘: "轆",
  辙: "轍",
  办: "辦",
  击: "擊",
  岁: "歲",
  异: "異",
  开: "開",
  关: "關",
  这: "這",
  进: "進",
  远: "遠",
  违: "違",
  连: "連",
  迟: "遲",
  适: "適",
  辽: "遼",
  遗: "遺",
  应: "應",
  疗: "療",
  苏: "蘇",
  范: "範",
  茧: "繭",
  荐: "薦",
  药: "藥",
  艺: "藝",
  蓦: "驀",
  战: "戰",
  灵: "靈",
  兽: "獸",
  秘: "秘",
  笈: "笈",
};

function convertToTraditional(text) {
  if (typeof text !== "string") return text;
  return text
    .split("")
    .map((char) => S2T_DICT[char] || char)
    .join("");
}

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

function getExistingNovels() {
  const novelsDir = path.join(TARGET_BASE_DIR, "novels");
  if (!fs.existsSync(novelsDir)) return [];
  const files = fs.readdirSync(novelsDir).filter((f) => f.endsWith(".md"));
  const list = [];
  files.forEach((file) => {
    try {
      const content = fs.readFileSync(path.join(novelsDir, file), "utf-8");
      const parsed = parseMarkdown(content);
      const title = parsed.frontmatter.title || path.basename(file, ".md");
      list.push(title);
    } catch (err) {
      // ignore
    }
  });
  return Array.from(new Set(list)).filter(Boolean);
}

async function promptNovel(defaultNovel) {
  const existingNovels = getExistingNovels();
  let novelChoice = "";
  if (existingNovels.length > 0) {
    console.log("\n請選擇此項目的所屬作品 (novel)：");
    existingNovels.forEach((n, idx) => {
      console.log(`  [${idx + 1}] ${n}`);
    });
    console.log(`  [${existingNovels.length + 1}] 手動輸入其他作品`);
    const ans = await question(
      `請輸入作品序號 (1-${existingNovels.length + 1}) [預設 1]: `,
    );
    const idx = parseInt(ans.trim(), 10) - 1;
    if (isNaN(idx) || idx === -1) {
      novelChoice = existingNovels[0];
    } else if (idx >= 0 && idx < existingNovels.length) {
      novelChoice = existingNovels[idx];
    } else {
      const customNovel = await question("請手動輸入所屬作品名稱：");
      novelChoice = customNovel.trim() || defaultNovel;
    }
  } else {
    const novel = await question(
      `所屬作品名稱 (novel) [預設: "${defaultNovel}"]: `,
    );
    novelChoice = novel.trim() || defaultNovel;
  }
  return convertToTraditional(novelChoice);
}

function getCollectionFields(collectionChoice) {
  const isKnownType = [
    "novels",
    "characters",
    "guoxue",
    "worldview",
    "factions",
    "items",
    "techniques",
    "bestiary",
  ].includes(collectionChoice);
  if (isKnownType) {
    return null;
  }
  const typeAstroPath = path.join(
    TARGET_BASE_DIR,
    "..",
    "pages",
    "shanzhuang",
    "[type].astro",
  );
  try {
    if (!fs.existsSync(typeAstroPath)) return null;
    const astroContent = fs.readFileSync(typeAstroPath, "utf-8");
    const startTag = `/* BEGIN_COLLECTION_${collectionChoice}_RENDER_CONFIG */`;
    const endTag = `/* END_COLLECTION_${collectionChoice}_RENDER_CONFIG */`;
    const startIndex = astroContent.indexOf(startTag);
    const endIndex = astroContent.indexOf(endTag);

    if (startIndex !== -1 && endIndex !== -1) {
      const block = astroContent.substring(
        startIndex + startTag.length,
        endIndex,
      );
      const fields = {};
      const matches = block.matchAll(
        /([a-zA-Z0-9_]+)\s*:\s*['"]([a-zA-Z0-9_]+)['"]/g,
      );
      for (const m of matches) {
        fields[m[1]] = m[2];
      }
      return fields;
    }
  } catch (err) {
    console.error(`[Astro 解析警告] 無法解析自訂欄位配置:`, err.message);
  }
  return null;
}

// 讀取小說工作區設定
let workspacePath = "";
if (fs.existsSync(CONFIG_FILE)) {
  try {
    const config = JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8"));
    workspacePath = config.workspacePath || "";
  } catch (err) {
    // 忽略讀取錯誤
  }
}

// 建立讀取介面
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});
const question = (query) =>
  new Promise((resolve) => rl.question(query, resolve));

// 彈出 Windows 原生 OpenFileDialog
function selectFilesViaWindows() {
  console.log(
    "正在為您開啟 Windows 檔案選擇視窗，請選擇要匯入的文檔 (支援 Shift/Ctrl 多選)...",
  );

  // 組合 PowerShell 指令，注意轉義與雙引號
  const escapedWorkspacePath = workspacePath
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"');
  const psScript = `
    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Multiselect = $true
    $dialog.Filter = 'Markdown 檔案 (*.md)|*.md|所有檔案 (*.*)|*.*'
    $initDir = [System.Environment]::GetFolderPath('MyDocuments')
    if (Test-Path '${escapedWorkspacePath}') { $initDir = '${escapedWorkspacePath}' }
    $dialog.InitialDirectory = $initDir
    $dialog.Title = '請選擇要匯入的小說或設定檔'
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $dialog.FileNames | ForEach-Object { Write-Output $_ }
    }
  `;

  try {
    // 將多行指令用分號連接，確保單行化時語法正確
    const formattedScript = psScript
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .join("; ");

    // 執行 PowerShell 並取得結果
    const output = execSync(
      `powershell -NoProfile -Command "${formattedScript}"`,
      { encoding: "utf8" },
    );
    const paths = output
      .split(/\r?\n/)
      .map((p) => p.trim())
      .filter(Boolean);
    return paths;
  } catch (err) {
    console.error("❌ 調用 Windows 檔案對話框失敗：", err.message);
    return [];
  }
}

// 簡易 YAML 解析器，分離 Frontmatter 與內文
function parseMarkdown(fileContent) {
  const lines = fileContent.split(/\r?\n/);
  let inFrontmatter = false;
  let frontmatterLines = [];
  let contentLines = [];
  let delimiterCount = 0;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (line.trim() === "---") {
      delimiterCount++;
      if (delimiterCount === 1) {
        inFrontmatter = true;
        continue;
      } else if (delimiterCount === 2) {
        inFrontmatter = false;
        continue;
      }
    }

    if (inFrontmatter) {
      frontmatterLines.push(line);
    } else {
      contentLines.push(line);
    }
  }

  // 解析簡單 YAML
  const yamlObj = {};
  const yamlStr = frontmatterLines.join("\n");
  const yamlLines = yamlStr.split("\n");
  let currentKey = null;
  let currentArray = null;

  for (const line of yamlLines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    if (trimmed.startsWith("-") && currentKey && currentArray) {
      let val = trimmed.substring(1).trim();
      if (
        (val.startsWith('"') && val.endsWith('"')) ||
        (val.startsWith("'") && val.endsWith("'"))
      ) {
        val = val.substring(1, val.length - 1);
      }
      currentArray.push(val);
      continue;
    }

    const colonIdx = line.indexOf(":");
    if (colonIdx !== -1) {
      const key = line.substring(0, colonIdx).trim();
      let value = line.substring(colonIdx + 1).trim();

      if (value === "") {
        currentKey = key;
        currentArray = [];
        yamlObj[key] = currentArray;
      } else {
        if (
          (value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))
        ) {
          value = value.substring(1, value.length - 1);
        }
        if (value.startsWith("[") && value.endsWith("]")) {
          yamlObj[key] = value
            .substring(1, value.length - 1)
            .split(",")
            .map((s) => s.replace(/['"]/g, "").trim())
            .filter(Boolean);
        } else {
          yamlObj[key] = value;
        }
        currentKey = null;
        currentArray = null;
      }
    }
  }

  return {
    frontmatter: yamlObj,
    content: contentLines.join("\n").trim(),
  };
}

// 將 JavaScript 物件轉換為 YAML Frontmatter 字串
function toYAML(obj) {
  let lines = ["---"];
  for (const [key, value] of Object.entries(obj)) {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        lines.push(`${key}: []`);
      } else {
        lines.push(`${key}:`);
        value.forEach((item) => {
          lines.push(`  - ${JSON.stringify(item)}`);
        });
      }
    } else {
      lines.push(`${key}: ${JSON.stringify(value)}`);
    }
  }
  lines.push("---");
  return lines.join("\n");
}

// 建立全站標題對照表，用於雙括號連結解析
function buildTitleMap() {
  const titleMap = new Map(); // title -> { collection, slug }
  const collections = [
    "novels",
    "characters",
    "worldview",
    "factions",
    "guoxue",
    "items",
    "techniques",
    "bestiary",
  ];

  collections.forEach((col) => {
    const dir = path.join(TARGET_BASE_DIR, col);
    if (!fs.existsSync(dir)) return;

    const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md"));
    files.forEach((file) => {
      try {
        const content = fs.readFileSync(path.join(dir, file), "utf-8");
        const parsed = parseMarkdown(content);
        const title =
          parsed.frontmatter.title ||
          parsed.frontmatter.name ||
          path.basename(file, ".md");
        const slug = path.basename(file, ".md");

        titleMap.set(title, { collection: col, slug });

        // 也將別名加入對照表
        if (parsed.frontmatter.alias) {
          const aliases = Array.isArray(parsed.frontmatter.alias)
            ? parsed.frontmatter.alias
            : [parsed.frontmatter.alias];
          aliases.forEach((a) => {
            if (a) titleMap.set(a, { collection: col, slug });
          });
        }
      } catch (err) {
        // 忽略個別檔案解析錯誤
      }
    });
  });

  return titleMap;
}

// 格式標準化管道 (Format Standardization Pipeline)
function standardizeMarkdown(content, titleMap) {
  // 1. 換行符轉為 \n，清除行尾空白
  let clean = content
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .split("\n")
    .map((line) => line.trimEnd())
    .join("\n")
    .trim();

  // 2. 雙括號連結轉為標準 Markdown 連結: [[厲絕鋒]] -> [厲絕鋒](/shanzhuang/characters/li-jue-feng)
  clean = clean.replace(
    /\[\[([^\]|#]+)(#[^\]|]+)?(?:\|([^\]]+))?\]\]/g,
    (match, baseTerm, anchor, aliasPart) => {
      const cleanBaseTerm = baseTerm.replace(/\.md$/i, "").trim();
      const cleanAnchor = anchor ? anchor.trim() : "";
      const aliasText = aliasPart ? aliasPart.replace(/^\|/, "").trim() : "";

      const matchInfo = titleMap.get(cleanBaseTerm);
      if (matchInfo) {
        const displayTitle = aliasText || cleanBaseTerm;
        return `[${displayTitle}](/shanzhuang/${matchInfo.collection}/${matchInfo.slug}${cleanAnchor})`;
      } else {
        console.warn(
          `\x1b[33m⚠️  [連結警告] 無法解析雙括號連結 "${match}"，降級為純文字。\x1b[0m`,
        );
        return aliasText || cleanBaseTerm;
      }
    },
  );

  return clean;
}

async function main() {
  const selectedPaths = selectFilesViaWindows();
  if (selectedPaths.length === 0) {
    console.log("未選擇任何檔案，操作已取消。");
    process.exit(0);
  }

  console.log(`\n您共選擇了 ${selectedPaths.length} 個文檔。`);

  const collections = [
    "novels",
    "characters",
    "worldview",
    "factions",
    "guoxue",
    "items",
    "techniques",
    "bestiary",
    // [ADD_NEW_COLLECTION_CLI_ARRAY_HERE]
  ];
  const collectionLabels = {
    novels: "小說連載 (novels)",
    characters: "人物設定 (characters)",
    worldview: "世界觀設定 (worldview)",
    factions: "勢力組織 (factions)",
    guoxue: "國學筆記 (guoxue)",
    items: "法寶神兵 (items)",
    techniques: "功法秘笈 (techniques)",
    bestiary: "靈獸妖魔 (bestiary)",
    // [ADD_NEW_COLLECTION_CLI_LABEL_HERE]
  };

  const titleMap = buildTitleMap();

  // Phase 1 預掃描：讀取所有選定檔案的 Frontmatter，動態加載到 titleMap 中
  console.log("\n⌛ [Phase 1] 正在預掃描選擇的檔案 Frontmatter...");
  for (const filePath of selectedPaths) {
    if (!fs.existsSync(filePath)) continue;
    try {
      const rawContent = fs.readFileSync(filePath, "utf-8");
      const { frontmatter } = parseMarkdown(rawContent);
      const fileName = path.basename(filePath);
      const baseName = path.basename(fileName, ".md");

      const tempCollection =
        frontmatter.category || frontmatter.collection || "novels";
      let tempTitle =
        frontmatter.title || frontmatter.name || baseName.replace(/^\d+_/g, "");
      tempTitle = convertToTraditional(tempTitle);
      const tempSlug = pinyinSlugify(tempTitle);

      titleMap.set(tempTitle, { collection: tempCollection, slug: tempSlug });

      if (frontmatter.alias) {
        const aliases = Array.isArray(frontmatter.alias)
          ? frontmatter.alias
          : [frontmatter.alias];
        aliases.forEach((a) => {
          if (a) {
            const tradAlias = convertToTraditional(a.trim());
            titleMap.set(tradAlias, {
              collection: tempCollection,
              slug: tempSlug,
            });
          }
        });
      }
    } catch (err) {
      console.warn(
        `⚠️ [預掃描警告] 無法解析檔案 ${path.basename(filePath)}:`,
        err.message,
      );
    }
  }
  console.log(
    `✓ [Phase 1] 預掃描完成，當前 titleMap 共有 ${titleMap.size} 個詞條。\n`,
  );

  for (let i = 0; i < selectedPaths.length; i++) {
    const filePath = selectedPaths[i];
    const fileName = path.basename(filePath);
    console.log(`\n====================================================`);
    console.log(`[${i + 1}/${selectedPaths.length}] 正在處理文檔: ${fileName}`);
    console.log(`----------------------------------------------------`);

    if (!fs.existsSync(filePath)) {
      console.error(`❌ [錯誤] 檔案不存在: ${filePath}`);
      continue;
    }

    const rawContent = fs.readFileSync(filePath, "utf-8");
    const { frontmatter, content } = parseMarkdown(rawContent);

    // 1. 選擇歸類分區
    let collectionChoice = "";
    while (true) {
      console.log("請選擇此文檔要歸類的網站分區:");
      collections.forEach((col, idx) => {
        console.log(`  [${idx + 1}] ${collectionLabels[col]}`);
      });
      const ans = await question(`請輸入分區序號 (1-${collections.length}): `);
      const idx = parseInt(ans.trim(), 10) - 1;
      if (idx >= 0 && idx < collections.length) {
        collectionChoice = collections[idx];
        break;
      }
      console.log("⚠️  輸入無效，請重新選擇。");
    }

    // 2. 引導補齊對應分區所需的欄位
    const baseName = path.basename(fileName, ".md");
    const todayStr = new Date().toISOString().split("T")[0];
    const data = { ...frontmatter };

    // 預設與公用欄位引導
    if (collectionChoice === "characters") {
      const defaultName = convertToTraditional(
        data.name || data.title || baseName.replace(/^\d+_/g, ""),
      );
      const name = await question(`人物名稱 (name) [預設: "${defaultName}"]: `);
      data.name = convertToTraditional(name.trim() || defaultName);

      data.novel = await promptNovel(data.novel || "長生劫");

      const defaultDesc = convertToTraditional(data.description || "暫無介紹");
      const desc = await question(
        `人物簡介 (description) [預設: "${defaultDesc}"]: `,
      );
      data.description = convertToTraditional(desc.trim() || defaultDesc);

      const defaultAlias = (data.alias || [data.name]).map((a) =>
        convertToTraditional(a),
      );
      const aliasInput = await question(
        `別名/稱號 (alias) (多個用逗號隔開) [預設: "${defaultAlias.join(", ")}"]: `,
      );
      if (aliasInput.trim()) {
        data.alias = aliasInput
          .split(/[,，、\s]+/)
          .map((s) => convertToTraditional(s.trim()))
          .filter(Boolean);
      } else {
        data.alias = defaultAlias;
      }
    } else if (collectionChoice === "items") {
      const defaultTitle = convertToTraditional(
        data.title || data.name || baseName.replace(/^\d+_/g, ""),
      );
      const title = await question(
        `法寶名稱 (title) [預設: "${defaultTitle}"]: `,
      );
      data.title = convertToTraditional(title.trim() || defaultTitle);

      const defaultRank = convertToTraditional(data.rank || "凡鐵");
      const rank = await question(`法寶品階 (rank) [預設: "${defaultRank}"]: `);
      data.rank = convertToTraditional(rank.trim() || defaultRank);

      data.novel = await promptNovel(data.novel || "長生劫");

      const defaultDesc = convertToTraditional(data.description || "暫無介紹");
      const desc = await question(
        `法寶簡介 (description) [預設: "${defaultDesc}"]: `,
      );
      data.description = convertToTraditional(desc.trim() || defaultDesc);
    } else if (collectionChoice === "techniques") {
      const defaultTitle = convertToTraditional(
        data.title || data.name || baseName.replace(/^\d+_/g, ""),
      );
      const title = await question(
        `功法名稱 (title) [預設: "${defaultTitle}"]: `,
      );
      data.title = convertToTraditional(title.trim() || defaultTitle);

      const defaultTechType = convertToTraditional(data.type || "內功");
      const techType = await question(
        `功法類型 (type，例如: 劍法、內功) [預設: "${defaultTechType}"]: `,
      );
      data.type = convertToTraditional(techType.trim() || defaultTechType);

      data.novel = await promptNovel(data.novel || "長生劫");

      const defaultDesc = convertToTraditional(data.description || "暫無介紹");
      const desc = await question(
        `功法簡介 (description) [預設: "${defaultDesc}"]: `,
      );
      data.description = convertToTraditional(desc.trim() || defaultDesc);
    } else if (collectionChoice === "bestiary") {
      const defaultTitle = convertToTraditional(
        data.title || data.name || baseName.replace(/^\d+_/g, ""),
      );
      const title = await question(
        `異獸名稱 (title) [預設: "${defaultTitle}"]: `,
      );
      data.title = convertToTraditional(title.trim() || defaultTitle);

      data.novel = await promptNovel(data.novel || "長生劫");

      const defaultDesc = convertToTraditional(data.description || "暫無介紹");
      const desc = await question(
        `靈獸簡介 (description) [預設: "${defaultDesc}"]: `,
      );
      data.description = convertToTraditional(desc.trim() || defaultDesc);
    } else {
      // novels, worldview, factions, guoxue 皆使用 title
      const defaultTitle = convertToTraditional(
        data.title || data.name || baseName.replace(/^\d+_/g, ""),
      );
      const title = await question(
        `文章標題 (title) [預設: "${defaultTitle}"]: `,
      );
      data.title = convertToTraditional(title.trim() || defaultTitle);

      if (collectionChoice === "novels") {
        const defaultDesc = convertToTraditional(
          data.description || `${data.title} - 大綱與劇本連載`,
        );
        const desc = await question(
          `小說簡介 (description) [預設: "${defaultDesc}"]: `,
        );
        data.description = convertToTraditional(desc.trim() || defaultDesc);

        const defaultStatus = data.status || "ongoing";
        const status = await question(
          `連載狀態 (status: ongoing, completed, hiatus) [預設: "${defaultStatus}"]: `,
        );
        data.status = convertToTraditional(status.trim() || defaultStatus);
      } else if (collectionChoice === "worldview") {
        const defaultCat = convertToTraditional(data.category || "世界觀");
        const cat = await question(
          `設定分類 (category，例如: 機制、地理、神明) [預設: "${defaultCat}"]: `,
        );
        data.category = convertToTraditional(cat.trim() || defaultCat);

        const defaultDesc = convertToTraditional(
          data.description || "暫無設定介紹",
        );
        const desc = await question(
          `設定簡介 (description) [預設: "${defaultDesc}"]: `,
        );
        data.description = convertToTraditional(desc.trim() || defaultDesc);
      } else if (collectionChoice === "factions") {
        const defaultCat = convertToTraditional(data.category || "勢力");
        const cat = await question(
          `勢力分類 (category，例如: 正派、地下、世俗) [預設: "${defaultCat}"]: `,
        );
        data.category = convertToTraditional(cat.trim() || defaultCat);

        const defaultDesc = convertToTraditional(
          data.description || "暫無勢力介紹",
        );
        const desc = await question(
          `勢力簡介 (description) [預設: "${defaultDesc}"]: `,
        );
        data.description = convertToTraditional(desc.trim() || defaultDesc);
      } else if (collectionChoice === "guoxue") {
        const defaultSrc = convertToTraditional(data.source || "未知");
        const source = await question(
          `文獻出處 (source) [預設: "${defaultSrc}"]: `,
        );
        data.source = convertToTraditional(source.trim() || defaultSrc);
      } else {
        // 自訂類別，自動引導
        const customFields = getCollectionFields(collectionChoice);
        if (customFields) {
          for (const [fieldName, fieldType] of Object.entries(customFields)) {
            if (fieldName === "novel") {
              data.novel = await promptNovel(data.novel || "長生劫");
            } else {
              const defaultVal = convertToTraditional(data[fieldName] || "");
              const inputVal = await question(
                `請輸入欄位 "${fieldName}" 的值 (${fieldType}) [預設: "${defaultVal}"]: `,
              );
              data[fieldName] = convertToTraditional(
                inputVal.trim() || defaultVal,
              );
            }
          }
        }
      }
    }

    // 發布日期欄位
    const defaultPubDate = data.pubDate || todayStr;
    const pubDate = await question(
      `發布日期 (pubDate: yyyy-mm-dd) [預設: "${defaultPubDate}"]: `,
    );
    data.pubDate = pubDate.trim() || defaultPubDate;

    // 3. 自動 Slugify 網頁別名
    const textForSlug =
      collectionChoice === "characters" ? data.name : data.title;
    const cleanSlug = pinyinSlugify(textForSlug);

    // 4. 執行標準化 Pipeline
    console.log(
      "\n⌛ 正在執行文檔標準化流程 (換行符標準化、雙括號連結轉譯)...",
    );
    const standardizedBody = standardizeMarkdown(content, titleMap);

    // 5. 組合並寫入檔案
    const finalFrontmatter = toYAML(data);
    const finalFileContent = `${finalFrontmatter}\n\n${standardizedBody}`;

    const targetDir = path.join(TARGET_BASE_DIR, collectionChoice);
    if (!fs.existsSync(targetDir)) {
      fs.mkdirSync(targetDir, { recursive: true });
    }
    const targetFilePath = path.join(targetDir, `${cleanSlug}.md`);

    fs.writeFileSync(targetFilePath, finalFileContent, "utf-8");
    console.log(
      `\x1b[32m✓ 匯入成功！檔案已寫入至: src/content/${collectionChoice}/${cleanSlug}.md\x1b[0m`,
    );

    // 更新本地 titleMap 以利後續匯入檔案能關聯此篇新文章
    const finalTitle =
      collectionChoice === "characters" ? data.name : data.title;
    titleMap.set(finalTitle, { collection: collectionChoice, slug: cleanSlug });
    if (data.alias) {
      const aliases = Array.isArray(data.alias) ? data.alias : [data.alias];
      aliases.forEach((a) => {
        if (a)
          titleMap.set(a, { collection: collectionChoice, slug: cleanSlug });
      });
    }
  }

  console.log(`\n🎉 所有選擇的文檔皆已處理並標準化匯入完成！`);
  rl.close();
}

main().catch((err) => {
  console.error("❌ 執行出錯:", err);
  if (rl) rl.close();
  process.exit(1);
});
