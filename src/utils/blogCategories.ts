export interface BlogCategoryInfo {
  id: 'tech' | 'daily' | 'thinking' | 'reading';
  name: string;
  slug: string;
  icon: string;
  badgeText: string;
  color: string;
  accentColor: string;
  description: string;
}

export const BLOG_CATEGORIES: Record<string, BlogCategoryInfo> = {
  tech: {
    id: 'tech',
    name: '技術筆記',
    slug: 'tech',
    icon: '⌨️',
    badgeText: '技',
    color: '#2d5f5a', // 青墨色
    accentColor: 'rgba(45, 95, 90, 0.12)',
    description: '既然轉不了系就在這個系的基礎上到處學有的沒的吧',
  },
  daily: {
    id: 'daily',
    name: '日常心得',
    slug: 'daily',
    icon: '🍵',
    badgeText: '日',
    color: '#8c6239', // 赭茶色
    accentColor: 'rgba(140, 98, 57, 0.12)',
    description: '單純紀錄生活中的事情，絕對不會有區區人的部分(吧?)',
  },
  thinking: {
    id: 'thinking',
    name: '思考練習',
    slug: 'thinking',
    icon: '♟️',
    badgeText: '思',
    color: '#4a5568', // 墨青灰
    accentColor: 'rgba(74, 85, 104, 0.12)',
    description: '想到就寫想到就寫，就只是個思考練習而已',
  },
  reading: {
    id: 'reading',
    name: '閱讀心得',
    slug: 'reading',
    icon: '📖',
    badgeText: '讀',
    color: '#9b2c2c', // 硃砂深紅
    accentColor: 'rgba(155, 44, 44, 0.12)',
    description: '被圖書館阿姨激到啦，怎麼說我看書都沒有看進去啦!?',
  },
};

export const BLOG_CATEGORY_LIST: BlogCategoryInfo[] = Object.values(BLOG_CATEGORIES);

export function getCategoryInfo(categoryId?: string): BlogCategoryInfo {
  if (categoryId && categoryId in BLOG_CATEGORIES) {
    return BLOG_CATEGORIES[categoryId];
  }
  return BLOG_CATEGORIES.daily;
}

/**
 * 自動內文摘要兜底函式 (Auto-excerpt)
 * 若文章未手動填寫 description，則自動自 Markdown 正文中擷取前 maxLen 個字
 */
export function getArticleExcerpt(post: { body?: string; data?: { description?: string } }, maxLen = 110): string {
  if (post?.data?.description && post.data.description.trim().length > 0) {
    return post.data.description.trim();
  }

  if (!post?.body) {
    return '';
  }

  // 清洗 Markdown 標記
  let clean = post.body
    .replace(/^---[\s\S]*?---/, '') // 移除 frontmatter
    .replace(/```[\s\S]*?```/g, '') // 移除代碼塊
    .replace(/`([^`]+)`/g, '$1') // 移除行內代碼標記
    .replace(/!\[.*?\]\(.*?\)/g, '') // 移除圖片
    .replace(/\[([^\]]+)\]\(.*?\)/g, '$1') // 移除超連結，保留錨文字
    .replace(/#{1,6}\s+[^\n]+/g, '') // 移除標題行
    .replace(/>\s+[^\n]+/g, '') // 移除引用行
    .replace(/[*_~=]/g, '') // 移除粗體、斜體、刪除線符號
    .replace(/\\/g, '') // 移除編輯器殘留之換行反斜線
    .replace(/\s+/g, ' ') // 合併多餘空白與換行
    .trim();

  if (!clean) {
    return '';
  }

  if (clean.length <= maxLen) {
    return clean;
  }

  return clean.slice(0, maxLen) + '…';
}

