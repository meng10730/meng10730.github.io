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
    description: '程式開發、前端架構探索與工程實踐的淬鍊。',
  },
  daily: {
    id: 'daily',
    name: '日常心得',
    slug: 'daily',
    icon: '🍵',
    badgeText: '日',
    color: '#8c6239', // 赭茶色
    accentColor: 'rgba(140, 98, 57, 0.12)',
    description: '柴米油鹽、浮生一日與生活細碎感悟的隨筆。',
  },
  thinking: {
    id: 'thinking',
    name: '思考練習',
    slug: 'thinking',
    icon: '♟️',
    badgeText: '思',
    color: '#4a5568', // 墨青灰
    accentColor: 'rgba(74, 85, 104, 0.12)',
    description: '邏輯推演、心智模型與自我思辨的深度整理。',
  },
  reading: {
    id: 'reading',
    name: '閱讀心得',
    slug: 'reading',
    icon: '📖',
    badgeText: '讀',
    color: '#9b2c2c', // 硃砂深紅
    accentColor: 'rgba(155, 44, 44, 0.12)',
    description: '開卷有得、典籍翻閱與書海對話的文字印記。',
  },
};

export const BLOG_CATEGORY_LIST: BlogCategoryInfo[] = Object.values(BLOG_CATEGORIES);

export function getCategoryInfo(categoryId?: string): BlogCategoryInfo {
  if (categoryId && categoryId in BLOG_CATEGORIES) {
    return BLOG_CATEGORIES[categoryId];
  }
  return BLOG_CATEGORIES.daily;
}
