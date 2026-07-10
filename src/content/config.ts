import { defineCollection, z } from "astro:content";

// 部落格文章
const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
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

// 山莊 → 人物設定
const characters = defineCollection({
  type: "content",
  schema: z.object({
    name: z.string(), // 人物名稱
    description: z.string().optional(), // 人物簡介 (用於懸浮氣泡)
    alias: z.array(z.string()).default([]), // 別名 / 江湖稱號
    affiliation: z.string().optional(), // 所屬門派或陣營 (指向 factions 的 slug)
    novel: z.string().optional(), // 所屬小說名稱（選填）
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

// [ADD_NEW_COLLECTION_DEFINITION_HERE]

export const collections = {
  blog,
  works,
  novels,
  characters,
  worldview,
  factions,
  guoxue,
  items,
  techniques,
  bestiary,

  // [ADD_NEW_COLLECTION_EXPORT_HERE]
};
