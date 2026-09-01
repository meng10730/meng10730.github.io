import { getCollection } from 'astro:content';

export async function getStaticPaths() {
  const allBooks = await getCollection('novels', (entry: any) => !entry.id.startsWith('_'));
  const allChapters = await getCollection('novel_chapters', (entry: any) => !entry.id.startsWith('_'));

  return allBooks.map((book) => {
    const bookId = book.id.replace(/\.[^/.]+$/, '');
    const cleanSlug = book.slug.replace(/[()（）\s]/g, '');
    const bookChapters = allChapters.filter((c) => {
      const b = c.data.book || '';
      return b === book.slug || 
             b === bookId || 
             b === book.data?.title || 
             b.replace(/[()（）\s]/g, '') === cleanSlug;
    });
    return {
      params: { book: book.slug },
      props: { book, chapters: bookChapters },
    };
  });
}

export async function GET({ props }: any) {
  const { book, chapters } = props;
  const sortedChapters = [...chapters].sort((a: any, b: any) => (a.data.order || 0) - (b.data.order || 0));

  // 預先處理每個章節的 HTML 渲染
  const renderedChapters = await Promise.all(
    sortedChapters.map(async (ch: any) => {
      const { Content } = await ch.render();
      return {
        slug: ch.slug,
        title: ch.data.title,
        book: ch.data.book,
        part: ch.data.part,
        volume: ch.data.volume,
        chapter: ch.data.chapter,
        section: ch.data.section,
        order: ch.data.order,
        body: ch.body,
      };
    })
  );

  return new Response(
    JSON.stringify({
      bookTitle: book.data.title,
      bookSlug: book.slug,
      total: renderedChapters.length,
      chapters: renderedChapters,
    }),
    {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );
}
