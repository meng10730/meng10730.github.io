import { defineCollection, z } from "astro:content";

// 部落格文章
const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum(["tech", "daily", "thinking", "reading"]).default("daily"),
    topic: z.string().optional(), // 文章核心主題或主要內容簡述
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
  }),
});

// 作品集專案
const works = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 專案名稱
    description: z.string(), // 一句話描述
    category: z.enum(["web", "game", "other"]), // 分類：web / game / other
    techs: z.array(z.string()).default([]), // 使用技術標籤
    status: z.enum(["completed", "ongoing", "archived"]).default("completed"), // 狀態
    github: z.string().url().optional(), // GitHub 連結（選填）
    demo: z.string().url().optional(), // Live Demo 連結（選填）
    pubDate: z.coerce.date(), // 完成或發布日期
  }),
});

// 山莊 → 小說發布
const novels = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 小說標題
    description: z.string(), // 簡介
    genre: z.array(z.string()).default([]), // 類型標籤（武俠、仙俠…）
    status: z.enum(["ongoing", "completed", "hiatus"]).default("ongoing"), // 連載狀態
    pubDate: z.coerce.date(), // 開始連載日期
    cover: z.string().optional(), // 封面圖路徑（選填）
  }),
});

const aliasItemSchema = z.union([
  z.string(),
  z.object({
    category: z
      .enum(["title", "realName", "courtesyName", "nickname", "other"])
      .default("title"),
    name: z.string().min(1).max(20),
  }),
]);

// 山莊 → 人物設定
const characters = defineCollection({
  type: "content",
  schema: z.object({
    name: z.string(), // 人物名稱
    description: z.string().nullish(), // 人物簡介 (用於懸浮氣泡)
    alias: z
      .array(aliasItemSchema)
      .default([])
      .refine(
        (items) => {
          const names = items
            .map((item) => (typeof item === "string" ? item : item?.name)?.trim())
            .filter((n): n is string => Boolean(n));
          return new Set(names).size === names.length;
        },
        { message: "角色別名名稱不能重複！請檢查並移除重複的稱號名稱。" }
      ), // 別名 / 江湖稱號 (支援舊字串與新結構化物件，並警示重複資料)
    affiliation: z.string().nullish(), // 所屬門派或陣營 (指向 factions 的 slug)
    novel: z.string().nullish(), // 所屬小說名稱（選填）
    tags: z.array(z.string()).default([]), // 標籤（主角、反派…）
    pubDate: z.coerce.date(), // 建立日期
  }),
});

// 山莊 → 世界觀設定
const worldview = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 設定標題
    description: z.string().optional(), // 設定簡介 (用於懸浮氣泡)
    category: z.string(), // 分類 (例如：機制, 地理, 神明體系)
    pubDate: z.coerce.date(), // 建立日期
  }),
});

// 山莊 → 勢力組織
const factions = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 勢力名稱
    description: z.string().optional(), // 勢力簡介 (用於懸浮氣泡)
    category: z.string(), // 分類 (例如：正派, 地下, 世俗, 中立)
    pubDate: z.coerce.date(), // 建立日期
  }),
});

// 山莊 → 國學筆記
const guoxue = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 筆記標題
    source: z.string().optional(), // 出處（論語、道德經…）
    category: z
      .enum([
        "confucianism",
        "taoism",
        "buddhism",
        "history",
        "poetry",
        "other",
      ])
      .default("other"), // 分類
    tags: z.array(z.string()).default([]),
    pubDate: z.coerce.date(),
  }),
});

// 山莊 → 法寶神兵
const items = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    novel: z.string().optional(),
    rank: z.string().optional(),
    pubDate: z.coerce.date(),
  }),
});

// 山莊 → 功法秘笈
const techniques = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    novel: z.string().optional(),
    type: z.string().optional(),
    pubDate: z.coerce.date(),
  }),
});

// 山莊 → 靈獸妖魔
const bestiary = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    novel: z.string().optional(),
    pubDate: z.coerce.date(),
  }),
});

// 山莊 → 典故引用字 (字庫考據)
const dictionary = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 單字標題，如 "璧"
    character: z.string().optional(), // 單字本身
    bopomofo: z.string().optional(), // 審定注音
    pinyin: z.string().optional(), // 漢語拼音
    initial: z.string().optional(), // 聲母分組（ㄅ、ㄇ、ㄈ...）
    radical: z.string().optional(), // 部首
    strokes: z.union([z.number(), z.string()]).optional(), // 筆畫
    source: z.string().optional(), // 主要經籍出處
    tags: z.array(z.string()).default([]),
    pubDate: z.coerce.date().default(() => new Date()),
  }),
});

// 山莊 → 小說連載小節
const novel_chapters = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(), // 小節標題（如：破廟殘燈）
    book: z.string().default("tianxia"), // 所屬小說作品 slug
    part: z
      .object({
        number: z.number().default(1), // 第幾部
        title: z.string().default("第一部"), // 部名稱
      })
      .default({ number: 1, title: "第一部" }),
    volume: z
      .object({
        number: z.number().default(1), // 第幾卷
        title: z.string().default("第一卷"), // 卷名稱
      })
      .default({ number: 1, title: "第一卷" }),
    chapter: z
      .object({
        number: z.number().default(1), // 第幾章
        title: z.string().default("第一章"), // 章名稱
      })
      .default({ number: 1, title: "第一章" }),
    section: z
      .object({
        number: z.number().default(1), // 第幾節
        title: z.string().default("第一節"), // 節名稱
      })
      .default({ number: 1, title: "第一節" }),
    order: z.number().default(1010101), // 全域精準排序代碼
    pubDate: z.coerce.date().default(() => new Date()), // 發布日期
  }),
});

// [ADD_NEW_COLLECTION_DEFINITION_HERE]

export const collections = {
  blog,
  works,
  novels,
  novel_chapters,
  characters,
  worldview,
  factions,
  guoxue,
  items,
  techniques,
  bestiary,
  dictionary,

  // [ADD_NEW_COLLECTION_EXPORT_HERE]
};

