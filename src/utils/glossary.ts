import { getCollection } from 'astro:content';

interface GlossaryItem {
  name: string;
  slug: string;
  type: 'characters' | 'worldview' | 'factions';
  desc: string;
  aliases: string[];
}

let cachedGlossary: GlossaryItem[] | null = null;

export async function getGlossary(): Promise<GlossaryItem[]> {
  if (cachedGlossary) return cachedGlossary;

  const charEntries = await getCollection('characters');
  const worldEntries = await getCollection('worldview');
  const factionEntries = await getCollection('factions');

  const list: GlossaryItem[] = [];

  // 輔助函式：過濾 Markdown 格式，提取前 60 字純文字作為摘要 fallback
  function extractSummary(content: string): string {
    if (!content) return '';
    // 1. 移除 Frontmatter
    let clean = content.replace(/^---[\s\S]*?---/, '');
    // 2. 移除 HTML 註解與 MDX 註解
    clean = clean.replace(/<!--[\s\S]*?-->/g, '');
    clean = clean.replace(/\{\/\*[\s\S]*?\*\/\}/g, '');
    // 3. 移除 Markdown 標題、連結、列表符號
    clean = clean.replace(/[#*`_~\[\]()\-]/g, ' ');
    // 4. 合併多餘空白並修剪
    clean = clean.replace(/\s+/g, ' ').trim();
    return clean.substring(0, 60);
  }

  for (const entry of charEntries) {
    if (entry.id.startsWith('_')) continue;
    const desc = entry.data.description || extractSummary(entry.body);
    list.push({
      name: entry.data.name,
      slug: entry.slug,
      type: 'characters',
      desc,
      aliases: Array.from(
        new Set(
          (entry.data.alias || [])
            .map((a: any) => (typeof a === 'string' ? a : a?.name)?.trim())
            .filter((n: any): n is string => Boolean(n))
        )
      ),
    });
  }

  for (const entry of worldEntries) {
    if (entry.id.startsWith('_')) continue;
    const desc = entry.data.description || extractSummary(entry.body);
    list.push({
      name: entry.data.title,
      slug: entry.slug,
      type: 'worldview',
      desc,
      aliases: [],
    });
  }

  for (const entry of factionEntries) {
    if (entry.id.startsWith('_')) continue;
    const desc = entry.data.description || extractSummary(entry.body);
    list.push({
      name: entry.data.title,
      slug: entry.slug,
      type: 'factions',
      desc,
      aliases: [],
    });
  }

  // 按文字長度由長到短排序，防止子字串提前被匹配（如“大煌王朝”優先於“大煌”匹配）
  list.sort((a, b) => b.name.length - a.name.length);

  cachedGlossary = list;
  return list;
}

export async function injectGlossary(htmlContent: string, currentSlug: string): Promise<string> {
  if (!htmlContent) return '';

  // A3: 將可能殘留的 broken-link 標籤直接還原為純文字
  let cleanedHtml = htmlContent.replace(/<span class="broken-link"[^>]*>(.*?)<\/span>/g, '$1');

  const glossary = await getGlossary();
  const glossaryApplied = new Set<string>(); // 紀錄此篇文章已匹配過的主條目 slug

  // 建立扁平化的關鍵字清單（包含主稱與別名）
  interface MatchItem {
    text: string;
    slug: string;
    type: string;
    desc: string;
  }

  const matchItems: MatchItem[] = [];

  for (const item of glossary) {
    if (item.slug === currentSlug) continue; // 排除自身

    // 主名稱
    matchItems.push({
      text: item.name,
      slug: item.slug,
      type: item.type,
      desc: item.desc,
    });

    // 別名
    for (const alias of item.aliases) {
      if (!alias) continue;
      matchItems.push({
        text: alias,
        slug: item.slug,
        type: item.type,
        desc: item.desc,
      });
    }
  }

  // 按關鍵字長度排序，確保長詞優先匹配
  matchItems.sort((a, b) => b.text.length - a.text.length);

  // HTML 屬性轉義，防範雙引號導致 HTML 毀損
  function escapeHtml(str: string): string {
    return str
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  // HTML 標籤保護拆分法：以 HTML 標籤做正則切分
  const parts = cleanedHtml.split(/(<\/?[^>]+>)/g);
  let insideLink = false;

  const newParts = parts.map(part => {
    // 若為 HTML 標籤，判定是否為 <a>，且直接回傳不處理
    if (part.startsWith('<')) {
      const lower = part.toLowerCase();
      if (lower.startsWith('<a ') || lower === '<a>') {
        insideLink = true;
      }
      if (lower === '</a>') {
        insideLink = false;
      }
      return part;
    }

    // 若處於超連結 <a> 標籤內部，直接跳過比對，避免 nested links
    if (insideLink) return part;

    let text = part;

    // 比對所有的關鍵字
    for (const match of matchItems) {
      if (glossaryApplied.has(match.slug)) continue; // A2: 此主條目（主稱或別名）只要已標記過，就跳過

      if (text.includes(match.text)) {
        const index = text.indexOf(match.text);
        if (index !== -1) {
          const left = text.substring(0, index);
          const right = text.substring(index + match.text.length);

          // 替換第一次出現的文字為帶有 data 屬性的 span
          text = left +
            `<span class="glossary-term" data-type="${match.type}" data-slug="${match.slug}" data-desc="${escapeHtml(match.desc)}">${match.text}</span>` +
            right;

          glossaryApplied.add(match.slug); // 標記為已套用
        }
      }
    }
    return text;
  });

  return newParts.join('');
}
