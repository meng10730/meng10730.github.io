import { defineCollection, z } from 'astro:content';

// 部落格文章
const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
  }),
});

// 作品集專案
const works = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),                                    // 專案名稱
    description: z.string(),                              // 一句話描述
    category: z.enum(['web', 'game', 'other']),           // 分類：web / game / other
    techs: z.array(z.string()).default([]),               // 使用技術標籤
    status: z.enum(['completed', 'ongoing', 'archived']).default('completed'), // 狀態
    github: z.string().url().optional(),                  // GitHub 連結（選填）
    demo: z.string().url().optional(),                    // Live Demo 連結（選填）
    pubDate: z.coerce.date(),                             // 完成或發布日期
  }),
});

// 山莊 → 小說發布
const novels = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),                                    // 小說標題
    description: z.string(),                              // 簡介
    genre: z.array(z.string()).default([]),               // 類型標籤（武俠、仙俠…）
    status: z.enum(['ongoing', 'completed', 'hiatus']).default('ongoing'), // 連載狀態
    pubDate: z.coerce.date(),                             // 開始連載日期
    cover: z.string().optional(),                         // 封面圖路徑（選填）
  }),
});

// 山莊 → 人物設定
const characters = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),                                     // 人物名稱
    alias: z.array(z.string()).default([]),               // 別名 / 江湖稱號
    affiliation: z.string().optional(),                   // 所屬門派或陣營
    novel: z.string().optional(),                         // 所屬小說名稱（選填）
    tags: z.array(z.string()).default([]),                // 標籤（主角、反派…）
    pubDate: z.coerce.date(),                             // 建立日期
  }),
});

// 山莊 → 國學筆記
const guoxue = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),                                    // 筆記標題
    source: z.string().optional(),                        // 出處（論語、道德經…）
    category: z.enum(['confucianism', 'taoism', 'buddhism', 'history', 'poetry', 'other']).default('other'), // 分類
    tags: z.array(z.string()).default([]),
    pubDate: z.coerce.date(),
  }),
});

export const collections = { blog, works, novels, characters, guoxue };
