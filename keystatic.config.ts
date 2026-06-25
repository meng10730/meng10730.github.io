import { config, fields, collection } from '@keystatic/core';

export default config({
  storage: import.meta.env.DEV
    ? { kind: 'github' as const, repo: 'meng10730/meng10730.github.io' }
    : { kind: 'cloud' as const },
  cloud: { project: 'meng10730/meng10730-github-io' },
  collections: {
    blog: collection({
      label: '部落格文章',
      slugField: 'title',
      path: 'src/content/blog/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '標題' } }),
        description: fields.text({ label: '簡介', multiline: true }),
        pubDate: fields.date({ label: '發布日期' }),
        tags: fields.array(fields.text({ label: '標籤' }), {
          label: '標籤',
          itemLabel: props => props.value,
        }),
        content: fields.mdx({ label: '內文', extension: 'md' }),
      },
    }),
    works: collection({
      label: '作品集專案',
      slugField: 'title',
      path: 'src/content/works/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '專案名稱' } }),
        description: fields.text({ label: '一句話描述' }),
        category: fields.select({
          label: '分類',
          options: [
            { label: 'Web', value: 'web' },
            { label: 'Game', value: 'game' },
            { label: 'Other', value: 'other' },
          ],
          defaultValue: 'web',
        }),
        techs: fields.array(fields.text({ label: '使用技術標籤' }), {
          label: '技術標籤',
          itemLabel: props => props.value,
        }),
        status: fields.select({
          label: '狀態',
          options: [
            { label: '已完成 (completed)', value: 'completed' },
            { label: '進行中 (ongoing)', value: 'ongoing' },
            { label: '已封存 (archived)', value: 'archived' },
          ],
          defaultValue: 'completed',
        }),
        github: fields.url({ label: 'GitHub 連結 (選填)' }),
        demo: fields.url({ label: 'Live Demo 連結 (選填)' }),
        pubDate: fields.date({ label: '完成或發布日期' }),
        content: fields.mdx({ label: '專案詳細介紹 (內文)', extension: 'md' }),
      },
    }),
    novels: collection({
      label: '小說連載 (山莊)',
      slugField: 'title',
      path: 'src/content/novels/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '小說標題' } }),
        description: fields.text({ label: '簡介', multiline: true }),
        genre: fields.array(fields.text({ label: '類型標籤 (武俠、仙俠…)' }), {
          label: '類型',
          itemLabel: props => props.value,
        }),
        status: fields.select({
          label: '連載狀態',
          options: [
            { label: '連載中 (ongoing)', value: 'ongoing' },
            { label: '已完結 (completed)', value: 'completed' },
            { label: '停更 (hiatus)', value: 'hiatus' },
          ],
          defaultValue: 'ongoing',
        }),
        pubDate: fields.date({ label: '開始連載日期' }),
        cover: fields.image({
          label: '封面圖',
          directory: 'public/images/novels',
          publicPath: '/images/novels',
        }),
        content: fields.mdx({ label: '內文 / 大綱', extension: 'md' }),
      },
    }),
    characters: collection({
      label: '人物設定 (山莊)',
      slugField: 'name',
      path: 'src/content/characters/*',
      format: { contentField: 'content' },
      schema: {
        name: fields.slug({ name: { label: '人物名稱' } }),
        alias: fields.array(fields.text({ label: '別名 / 江湖稱號' }), {
          label: '別名',
          itemLabel: props => props.value,
        }),
        affiliation: fields.text({ label: '所屬門派或陣營' }),
        novel: fields.text({ label: '所屬小說名稱' }),
        tags: fields.array(fields.text({ label: '標籤 (主角、反派…)' }), {
          label: '標籤',
          itemLabel: props => props.value,
        }),
        pubDate: fields.date({ label: '建立日期' }),
        content: fields.mdx({ label: '詳細人物傳記 / 設定', extension: 'md' }),
      },
    }),
    worldview: collection({
      label: '世界觀設定 (山莊)',
      slugField: 'title',
      path: 'src/content/worldview/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '設定標題' } }),
        category: fields.text({ label: '分類 (例：機制、地理、神明體系)' }),
        pubDate: fields.date({ label: '建立日期' }),
        content: fields.mdx({ label: '詳細設定內文', extension: 'md' }),
      },
    }),
    factions: collection({
      label: '勢力組織 (山莊)',
      slugField: 'title',
      path: 'src/content/factions/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '勢力名稱' } }),
        category: fields.text({ label: '分類 (例：正派、地下、世俗、中立)' }),
        pubDate: fields.date({ label: '建立日期' }),
        content: fields.mdx({ label: '詳細勢力內文', extension: 'md' }),
      },
    }),
    guoxue: collection({
      label: '國學筆記 (山莊)',
      slugField: 'title',
      path: 'src/content/guoxue/*',
      format: { contentField: 'content' },
      schema: {
        title: fields.slug({ name: { label: '筆記標題' } }),
        source: fields.text({ label: '出處 (論語、道德經…)' }),
        category: fields.select({
          label: '分類',
          options: [
            { label: '儒家 (confucianism)', value: 'confucianism' },
            { label: '道家 (taoism)', value: 'taoism' },
            { label: '佛家 (buddhism)', value: 'buddhism' },
            { label: '史學 (history)', value: 'history' },
            { label: '詩詞 (poetry)', value: 'poetry' },
            { label: '其他 (other)', value: 'other' },
          ],
          defaultValue: 'other',
        }),
        tags: fields.array(fields.text({ label: '標籤' }), {
          label: '標籤',
          itemLabel: props => props.value,
        }),
        pubDate: fields.date({ label: '建立日期' }),
        content: fields.mdx({ label: '筆記內文', extension: 'md' }),
      },
    }),
  },
});
